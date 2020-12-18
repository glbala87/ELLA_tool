#!/usr/bin/env python3

import datetime
import hashlib
import json
import logging
import logging.config
import time
from base64 import b64decode
from enum import Enum
from functools import wraps
from operator import itemgetter
from pathlib import Path
from socket import timeout as SocketTimeout
from typing import Dict, List, Mapping, Optional, Sequence, Tuple, Union

import click
import requests
from digitalocean import Droplet, Manager
from paramiko import SSHClient
from paramiko.buffered_pipe import PipeTimeout
from paramiko.client import AutoAddPolicy
from paramiko.rsakey import RSAKey
from paramiko.ssh_exception import NoValidConnectionsError
from requests.exceptions import ConnectionError, ConnectTimeout
from scp import SCPClient

logger_name = Path(__file__).stem
log_config = {
    "version": 1,
    "formatters": {"standard": {"format": "%(asctime)s [%(levelname)s] %(name)s: %(message)s"}},
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "level": "DEBUG",
            "formatter": "standard",
            "stream": "ext://sys.stderr",
        }
    },
    "loggers": {logger_name: {"handlers": ["console"], "level": "INFO"}},
}
logging.config.dictConfig(log_config)
logger = logging.getLogger(logger_name)

default_region = "fra1"
default_size = "s-1vcpu-2gb"
default_droplet_image = "docker-20-04"
default_tag = "gitlab-review-app"

revapp_run = """
docker inspect revapp >/dev/null 2>&1 && docker rm -f revapp
docker run -d \
--name revapp \
-e ANALYSES_PATH="/ella/src/vardb/testdata/analyses/default/" \
-e ATTACHMENT_STORAGE="/ella/src/vardb/testdata/attachments/" \
-e DEV_IGV_CYTOBAND=https://s3.amazonaws.com/igv.broadinstitute.org/genomes/seq/b37/b37_cytoband.txt \
-e DEV_IGV_FASTA=https://s3.amazonaws.com/igv.broadinstitute.org/genomes/seq/1kg_v37/human_g1k_v37_decoy.fasta \
-e ELLA_CONFIG=/ella/example_config.yml \
-e IGV_DATA="/ella/src/vardb/testdata/igv-data/" \
-e PGDATA=/pg-data \
-e PGHOST=/socket \
-e PORT=5000 \
-e PRODUCTION=false \
-e VIRTUAL_HOST={hostname} \
-p 80:5000 \
{image_name} && \
docker exec revapp make dbreset
""".strip()


class RevappStatus(str, Enum):
    OK = "OK"
    ServerError = "ServerError / Loading"
    NotRunning = "Not Running"
    TimedOut = "Timed Out"
    Down = "Down"

    def __str__(self) -> str:
        return self.value


droplet_attrs = ("id", "name", "created_at", "status", "ip_address")
droplet_details = (
    ("region", ("name", "slug")),
    ("size", ("slug", "memory", "vcpus", "disk")),
    ("networks", False),
    ("features", False),
    ("image", ("id", "name", "slug", "distribution")),
)

scp_bar_percent = 0.05
scp_bar_padding = int(1 / scp_bar_percent)
ssh_max_retries = 3
ssh_default_timeout = 60

# set up firewall on droplet to only listen on 22, 80 and 443
ufw_configs = list((Path(__file__).parent / "demo").glob("user*.rules"))
# expected output from correctly configured `ufw status`
ufw_status_ok = """
Status: active

To                         Action      From
--                         ------      ----
22/tcp                     LIMIT       Anywhere                  
80/tcp                     ALLOW       Anywhere                  
443/tcp                    ALLOW       Anywhere                  
22/tcp (v6)                LIMIT       Anywhere (v6)             
80/tcp (v6)                ALLOW       Anywhere (v6)             
443/tcp (v6)               ALLOW       Anywhere (v6)
""".strip()  # noqa: W291


class RetriesExceeded(Exception):
    err_list: List[Exception] = []

    def __init__(self, max_retries: int, errors=[], msg: str = None, args=[], kwargs={}):
        if msg is not None:
            self.msg = msg.format(max_retries=max_retries, *args, **kwargs)
        else:
            self.msg = f"Command failed after exceeding {max_retries} retries"
        super().__init__(msg)
        self.err_list = errors


### utility funcs


def retry(catch_exc, max_retries: int = ssh_max_retries, delay: int = 15, err_msg: str = None):
    if isinstance(catch_exc, Exception):
        catch_exc = (catch_exc,)

    def try_again(attempt_num):
        return attempt_num <= max_retries

    def deco_retry(f):
        @wraps(f)
        def f_retry(*args, **kwargs):
            retry_num = 0
            err_list = []
            while try_again(retry_num):
                try:
                    return f(*args, **kwargs)
                except catch_exc as e:
                    err_list.append(e)
                    backoff = delay * 2 ** retry_num
                    logger.error(f"{type(e).__name__}: {e}")
                    retry_num += 1
                    if try_again(retry_num):
                        logger.warning(f"Attempting retry #{retry_num} in {backoff}s")
                        time.sleep(backoff)
            raise RetriesExceeded(max_retries, err_list, err_msg, args, kwargs)

        return f_retry

    return deco_retry


def str2key(ctx, param: click.Parameter, value: str) -> RSAKey:
    key_file = Path(value)
    if not key_file.exists():
        raise click.BadParameter(f"Key {value} does not exist")
    rsa_key = RSAKey.from_private_key(key_file.open())
    return rsa_key


def str2list(ctx, param: click.Parameter, value: Optional[str]) -> List[str]:
    if value is None:
        return []
    new_list = [f for f in value.split(",") if f != ""]
    if len(new_list):
        return new_list
    raise click.BadParameter(f"invalid value '{value}' received for {param.human_readable_name}'")


def str2path(ctx, param, value: str) -> Path:
    return Path(value) if value is not None else None


### funcs


def fingerprint_key(pubkey: str) -> str:
    """ generates the md5 hexdigest of the public key used by digitalocean """
    pub_digest = hashlib.md5(b64decode(pubkey.encode("utf-8"))).hexdigest()
    return ":".join([pub_digest[i : i + 2] for i in range(0, len(pub_digest), 2)])


def format_name(ctx, param, value: str) -> str:
    if not value.startswith("revapp-"):
        value = f"revapp-{value}"
    return value


def get_droplet(mgr: Manager, name: str, tag: str = default_tag) -> Optional[Droplet]:
    logger.debug(f"Fetching droplet named {name}")
    all_drops = list_droplets(mgr, tag)
    by_name = [d for d in all_drops if d.name == name]
    if len(by_name) == 0:
        logger.info(f"No droplet found with name {name}")
        return None
    elif len(by_name) > 1:
        raise ValueError(f"Found multiple droplets named: {name}")
    return by_name[0]


@retry(
    (TimeoutError, NoValidConnectionsError),
    err_msg="Failed to connect to {2}@{1} after {max_retries}",
)
def get_ssh_conn(hostname: str, pkey: RSAKey, username: str = "root") -> SSHClient:
    logger.debug(f"Creating ssh connection to {hostname}")
    ssh = SSHClient()
    ssh.set_missing_host_key_policy(AutoAddPolicy)

    ssh.connect(hostname, username=username, pkey=pkey, allow_agent=False, look_for_keys=False)
    return ssh


def list_droplets(mgr: Manager, tag: str = default_tag) -> Sequence[Droplet]:
    logger.debug(f"Fetching all droplets with tag {tag}")
    all_drops = mgr.get_all_droplets(tag_name=tag)
    return all_drops


def print_table(
    data: Sequence[Union[Sequence, Mapping]],
    header: Sequence[Sequence] = [],
    min_width: int = 6,
    sep_char: str = "=",
) -> None:
    new_header = [str(x) for x in header]
    max_lens = [len(x) for x in new_header]
    new_data: List[List[str]] = []
    for rn, row in enumerate(data[:]):
        new_row = list()
        if isinstance(row, dict):
            if not header:
                raise ValueError("You must include a header if printing a dict")
            for i, h in enumerate(header):
                h_str = str(row.get(h, ""))
                dlen = len(h_str)
                if dlen > max_lens[i]:
                    max_lens[i] = dlen
                new_row.append(h_str)
        elif isinstance(row, (tuple, list)):
            for i, d in enumerate(row):
                d_str = str(d)
                d_len = len(d_str)
                if i + 1 > len(max_lens):
                    max_lens.append(d_len)
                elif len(d) > max_lens[i]:
                    max_lens[i] = d_len
        new_data.append(new_row)
    for i, val in enumerate(max_lens[:]):
        val += 1  # a little extra padding
        if val < min_width:
            val = min_width
        max_lens[i] = val
    if header:
        sep_row = [sep_char * i for i in max_lens]
        new_data = list([new_header, sep_row]) + new_data
    for row in new_data:
        for i, cell in enumerate(row):
            end_char = "  " if i < len(row) - 1 else "\n"
            print(f"{cell : <{max_lens[i]}}", end=end_char)


def provision_droplet(droplet: Droplet, pkey: RSAKey, image_name: str):
    ssh = get_ssh_conn(droplet.ip_address, pkey)
    # TODO: add option to show progress bar, is too noisy for runner loggers
    # scp = SCPClient(ssh.get_transport(), progress=scp_progress)
    scp = SCPClient(ssh.get_transport())

    provision_ufw(ssh, scp)
    logger.info(f"pulling image {image_name}")
    ssh_exec(ssh, f"docker pull {image_name}", timeout=300)
    logger.info(f"Starting application")
    ssh_exec(ssh, revapp_run.format(hostname=droplet.ip_address, image_name=image_name))
    logger.info(f"Completed provisioning and starting of {droplet.name}")


def provision_ufw(ssh: SSHClient, scp: SCPClient):
    logger.debug(f"Checking ufw status")
    msg, err = ssh_exec(ssh, "ufw status")
    if msg.strip() == ufw_status_ok:
        logger.info(f"ufw status ok, skipping")
        return

    logger.debug(f"moving current ufw configs")
    for ufw_conf in ufw_configs:
        ssh_exec(ssh, f"mv /etc/ufw/{ufw_conf.name} /etc/ufw/{ufw_conf.name}.old")
    scp_put(scp, ufw_configs, remote_path="/etc/ufw/")
    logger.debug(f"reloading ufw config")
    ssh_exec(ssh, "ufw reload")
    msg, err = ssh_exec(ssh, "ufw status")
    if msg.strip() != ufw_status_ok:
        raise ValueError(f"ufw status not matching after update: {msg}")
    logger.info(f"ufw successfully configured")


def scp_progress(filename: str, size: int, sent: int) -> None:
    percent = sent / size
    bar = int(percent // scp_bar_percent) * "=" + ">"
    print(f"{filename}: {percent*100:.2f}% |{bar: <{scp_bar_padding}}|", end="\r")


# TODO: narrow down what exceptions this might throw
@retry(Exception)
def scp_put(scp: SCPClient, files: Union[Path, Sequence[Path]], **kwargs):
    if isinstance(files, Path):
        put_files = [str(files)]
    else:
        put_files = [str(f) for f in files]
    str_files = ", ".join(put_files)
    xfer_start = datetime.datetime.now()
    try:
        scp.put(put_files, **kwargs)
    except Exception as e:
        xfer_total = datetime.datetime.now() - xfer_start
        logger.error(f"Transfer of {str_files} failed after {xfer_total}")
        raise e
    xfer_total = datetime.datetime.now() - xfer_start
    logger.info(f"Finished uploading file(s) {str_files} after {xfer_total}")


@retry((SocketTimeout, PipeTimeout), err_msg="SSH cmd '{1}' failed after {max_retries}")
def ssh_exec(ssh: SSHClient, cmd: str, **kwargs) -> Tuple[str, str]:
    """ use to get nicer output from SSHClient.exec_command """
    logger.debug(f"Executing '{cmd}'")
    if "timeout" not in kwargs:
        kwargs["timeout"] = ssh_default_timeout

    _, stdout, stderr = ssh.exec_command(cmd, **kwargs)
    out_str: str = stdout.read().decode("utf-8").strip()
    err_str: str = stderr.read().decode("utf-8").strip()
    logger.debug(f"output: {out_str}")
    logger.debug(f"error:  {err_str}")
    return out_str, err_str


def remove_droplet(mgr: Manager, name: Optional[str] = None, droplet: Optional[Droplet] = None):
    if droplet is None:
        if name:
            droplet = get_droplet(mgr, name)
            if droplet is None:
                raise ValueError(f"No droplet with name {name}")
        else:
            raise ValueError("Must give a droplet name or Droplet object to destroy")

    try:
        # make sure we've got the most recent droplet object
        droplet.load()
    except Exception as e:
        # check if already deleted or something?
        logger.error(f"Error attempting remove droplet {droplet.name} id {droplet.id}: {e}")
        raise e

    res = droplet.destroy()
    if res is True:
        logger.info(f"Destroyed droplet {droplet.name} (id {droplet.id}) successfully")
    else:
        breakpoint()
        pass


def revapp_status(droplet: Droplet) -> RevappStatus:
    url = f"http://{droplet.ip_address}"
    try:
        resp = requests.get(url, timeout=3)
    except ConnectionError as e:
        if "[Errno 111] Connection refused" in str(e):
            return RevappStatus.NotRunning
        elif "[Errno -2] Name or service not known" in str(e):
            return RevappStatus.Down
        elif isinstance(e, ConnectTimeout) or "[Errno 110] Connection timed out" in str(e):
            return RevappStatus.TimedOut
        raise e
    if resp.ok:
        return RevappStatus.OK
    return RevappStatus.ServerError


def trim_droplet(drop: Droplet, detailed=False) -> Dict:
    new_drop = {a: getattr(drop, a) for a in droplet_attrs}
    if detailed:
        for (key, vals) in droplet_details:
            if key not in drop:
                logger.warn(f"Could not find {key} attr in droplet {drop.name}/{drop.id}")
                continue
            if vals:
                new_drop[key] = dict()
                for v in vals:  # type: ignore
                    new_drop[key][v] = drop[key].get(v)
            else:
                new_drop[key] = drop[key]
    return new_drop


# click/CLI command functions


@click.group()
@click.option(
    "--token",
    envvar="DO_TOKEN",
    required=True,
    help="DigitalOcean API token (must have RW privilege)",
)
@click.option("--verbose", "-v", is_flag=True, help="set log level to INFO")
@click.option("--debug", "-D", is_flag=True, help="set log level to DEBUG")
@click.pass_context
def app(ctx, token: str, verbose: bool, debug: bool):
    if debug:
        logger.setLevel(logging.DEBUG)
    elif verbose:
        logger.setLevel(logging.INFO)
    ctx.obj["token"] = token
    ctx.obj["mgr"] = Manager(token=token)


@app.command(help="create a new droplet to run the review app")
@click.argument("name", envvar="REVAPP_NAME", callback=format_name)
@click.option(
    "--droplet-size",
    "size",
    envvar="REVAPP_SIZE",
    default=default_size,
    help="size slug for the droplet",
)
@click.option(
    "--image-name",
    envvar="REVAPP_IMAGE_NAME",
    required=True,
    help="name and tag of the tarred docker image",
)
@click.option(
    "--ssh-key",
    envvar="REVAPP_SSH_KEY",
    callback=str2key,
    required=True,
    help="path to ssh private key to add to the review app (must be in digitalocean)",
)
@click.option(
    "--replace",
    envvar="REVAPP_REPLACE",
    type=click.BOOL,
    is_flag=True,
    help="replace review app of the same name, if found",
)
@click.pass_context
def create(ctx, name: str, size: str, image_name: str, ssh_key: RSAKey, replace: bool) -> None:
    """ creates a new droplet to run the review app """
    exists = get_droplet(ctx.obj["mgr"], name)
    if exists:
        logger.info(f"Found existing droplet with name {name}: id {exists.id}")
        if not replace:
            raise ValueError(f"Review app for {name} already exists. Remove it or use --replace")
        remove_droplet(ctx.obj["mgr"], name)

    droplet_args = {
        "token": ctx.obj["token"],
        "name": name,
        "region": default_region,
        "size": size,
        "image": default_droplet_image,
        "tags": [default_tag],
        "ssh_keys": [fingerprint_key(ssh_key.get_base64())],
        "private_networking": True,
    }

    logger.debug(
        f"creating droplet with args {json.dumps({k: v for k, v in droplet_args.items() if k != 'token'})}"
    )
    droplet = Droplet(**droplet_args)
    droplet.create()

    while droplet.status is None or droplet.ip_address is None:
        time.sleep(5)
        try:
            droplet.load()
        except Exception as e:
            raise e
    logger.info(f"droplet {droplet.name} ready on {droplet.ip_address}")

    provision_droplet(droplet, ssh_key, image_name)


# this won't work wtf
@app.command(help="re-provision an existing review app")
@click.argument("name", envvar="REVAPP_NAME", callback=format_name)
@click.option(
    "--image-name",
    envvar="IMAGE_NAME",
    required=True,
    help="name and tag of the tarred docker image",
)
@click.option(
    "--ssh-key",
    envvar="REVAPP_SSH_KEY",
    callback=str2key,
    required=True,
    help="path to ssh private key to add to the review app (must be in digitalocean)",
)
@click.pass_context
def provision(ctx, name: str, image_name: str, ssh_key: RSAKey):
    # TODO: set timeout option on digitalocean side
    logger.info(f"Re-provisioning name {name}")
    droplet = get_droplet(ctx.obj["mgr"], name)
    if droplet is None or droplet.status != "active":
        raise ValueError(f"Cannot re-provision a stopped or non-existent droplet: {name}")
    provision_droplet(droplet, ssh_key, image_name)


@app.command(help="get the status of review app by branch name")
@click.argument("name", envvar="REVAPP_NAME", callback=format_name)
@click.option("--json", "json_format", is_flag=True, help="output in json format")
@click.option(
    "--fields",
    "-f",
    metavar="field1[,field2,...]",
    callback=str2list,
    help="restrict output to the selected fields",
)
@click.pass_context
def status(ctx, name: str, json_format: bool, fields: List[str]):
    droplet = get_droplet(ctx.obj["mgr"], name)
    if droplet is None:
        logger.error(f"No review app found named: {name}")
        if json_format:
            print("{}")
        return

    status_map = {
        "name": {"value": name, "format": "{}:"},
        "ip_address": {"value": droplet.ip_address, "format": "@ {}"},
        "droplet_status": {"value": droplet.status, "format": "{} (droplet)"},
        "app_status": {"value": revapp_status(droplet), "format": "{} (review app)"},
        "created_at": {"value": droplet.created_at, "format": "created at {}"},
    }
    if fields and len(fields):
        bad_fields = [f for f in fields if f not in status_map]
        if any(bad_fields):
            bad_field_str = ", ".join(bad_fields)
            good_field_str = ", ".join(status_map.keys())
            plural = "s" if len(bad_fields) > 1 else ""
            raise ValueError(
                f"Invalid field{plural}: {bad_field_str}. Must be one of: {good_field_str}"
            )
        for fname in list(status_map.keys()):
            if fname not in fields:
                del status_map[fname]

    if json_format:
        print(json.dumps({k: v["value"] for k, v in status_map.items()}))
    else:
        if len(status_map) == 1:
            print(list(status_map.values())[0]["value"])
        else:
            output_str = " ".join([v["format"].format(v["value"]) for v in status_map.values()])
            print(output_str)


@app.command(help="list all active review apps", name="list")
@click.option("--json", "json_format", is_flag=True, help="output in json format")
@click.option(
    "--details", "detailed", is_flag=True, help="give detailed droplet info (implies --json)"
)
@click.option("--sort", "sort_key", type=click.Choice(droplet_attrs, False), default="name")
@click.pass_context
def list_apps(ctx, json_format: bool, detailed: bool, sort_key: str):
    raw_droplets = list_droplets(ctx.obj["mgr"])
    trimmed = sorted([trim_droplet(d) for d in raw_droplets], key=itemgetter(sort_key))
    if not json_format and not detailed:
        print_table(trimmed, droplet_attrs)
    else:
        print(json.dumps(trimmed, indent=4))


@app.command(help="remove an existing review app droplet")
@click.argument("name", envvar="REVAPP_NAME", callback=format_name)
@click.pass_context
def remove(ctx, name: str) -> None:
    """ removes an existing review app droplet """
    remove_droplet(ctx.obj["mgr"], name)


if __name__ == "__main__":
    app(obj={})
