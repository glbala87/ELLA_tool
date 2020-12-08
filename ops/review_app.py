#!/usr/bin/env python3

import hashlib
import json
import logging
import logging.config
import time
from base64 import b64decode
from operator import itemgetter
from pathlib import Path
from typing import Any, Dict, List, Mapping, Optional, Tuple, Union, Sequence

import click
from digitalocean import Droplet, Manager
from digitalocean.baseapi import REQUEST_TIMEOUT_ENV_VAR
from paramiko import SSHClient, SSHException
from paramiko.client import AutoAddPolicy
from paramiko.rsakey import RSAKey
from scp import SCPClient

REQUIRED_ARGS = ("token", "name", "size", "image")
OPTIONAL_ARGS = ("tags", "ssh_keys")

default_region = "fra1"
default_size = "s-2vcpu-2gb"
default_image = "docker-20-04"
default_tag = "gitlab-review-app"
default_create_args = {
    "region": default_region,
    "size": default_size,
    "image": default_image,
    "tags": [default_tag],
}

revapp_run = """
docker run -d \
--name revapp \
-e ELLA_CONFIG=/ella/example_config.yml \
-e IGV_DATA="/ella/src/vardb/testdata/igv-data/" \
-e DEV_IGV_FASTA=https://s3.amazonaws.com/igv.broadinstitute.org/genomes/seq/1kg_v37/human_g1k_v37_decoy.fasta \
-e DEV_IGV_CYTOBAND=https://s3.amazonaws.com/igv.broadinstitute.org/genomes/seq/b37/b37_cytoband.txt \
-e ANALYSES_PATH="/ella/src/vardb/testdata/analyses/default/" \
-e ATTACHMENT_STORAGE="/ella/src/vardb/testdata/attachments/" \
-e PRODUCTION=false \
-e DEV_IGV_FASTA=https://s3.amazonaws.com/igv.broadinstitute.org/genomes/seq/1kg_v37/human_g1k_v37_decoy.fasta \
-e DEV_IGV_CYTOBAND=https://s3.amazonaws.com/igv.broadinstitute.org/genomes/seq/b37/b37_cytoband.txt \
-e VIRTUAL_HOST={hostname} \
-e PORT=5000 \
-p 5000:80 \
{image_name} \
supervisord -c /ella/ops/demo/supervisor.cfg && \
docker exec revapp make dbreset
""".strip()

droplet_attrs = ("id", "name", "created_at", "status", "ip_address")
droplet_details = (
    ("region", ("name", "slug")),
    ("size", ("slug", "memory", "vcpus", "disk")),
    ("networks", False),
    ("features", False),
    ("image", ("id", "name", "slug", "distribution")),
)

ufw_configs = list(Path("demo").glob("user*.rules"))
log_config = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {"standard": {"format": "%(asctime)s [%(levelname)s] %(name)s: %(message)s"}},
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "level": "INFO",
            "formatter": "standard",
            "stream": "ext://sys.stderr",
        }
    },
    "loggers": {"": {"handlers": ["console"], "level": "INFO"}},
}
logging.config.dictConfig(log_config)
logger = logging.getLogger(__name__)


### funcs


def fingerprint_key(pubkey: str) -> str:
    """ generates the md5 hexdigest of the public key used by digitalocean """
    pub_digest = hashlib.md5(b64decode(pubkey.encode("utf-8"))).hexdigest()
    return ":".join([pub_digest[i : i + 2] for i in range(0, len(pub_digest), 2)])


def format_name(ctx, param, value: str) -> str:
    if not value.startswith("revapp-"):
        value = f"revapp-{value}"
    return value


def get_droplet(mgr: Manager, name: str, tag: str = default_tag) -> Droplet:
    logger.info(f"Fetching droplet named {name}")
    all_drops = list_droplets(mgr, tag)
    by_name = [d for d in all_drops if d.name == name]
    if len(by_name) == 0:
        return
    elif len(by_name) > 1:
        raise ValueError(f"Found multiple droplets named: {name}")
    return by_name[0]


def get_ssh_conn(hostname: str, pkey: RSAKey, username: str = "root") -> SSHClient:
    ssh = SSHClient()
    ssh.set_missing_host_key_policy(AutoAddPolicy)
    ssh.connect(hostname, username=username, pkey=pkey, allow_agent=False, look_for_keys=False)
    return ssh


def list_droplets(mgr: Manager, tag: str = default_tag) -> Sequence[Droplet]:
    logger.info(f"Fetching all droplets with tag {tag}")
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
            end_char = "\t" if i < len(row) - 1 else "\n"
            print(f"{cell : <{max_lens[i]}}", end=end_char)


def provision_droplet(droplet: Droplet, args: Dict[str, Any]):
    ssh = get_ssh_conn(droplet.ip_address, args["pkey"])
    scp = SCPClient(ssh.get_transport(), progress=scp_progress)
    logger.info(f"moving old ufw configs")
    for ufw_conf in ufw_configs:
        ssh_exec(ssh, f"mv /etc/ufw/{ufw_conf.name} /etc/ufw/{ufw_conf.name}.old")
    logger.info(f"uploading new configs")
    scp.put(list(ufw_configs), remote_path="/etc/ufw/")
    logger.info(f"reloading ufw config")
    ssh_exec(ssh, "ufw reload")
    if args.get("image_tar"):
        logger.info(f"uploading image {args['image_tar']}")
        scp.put(args["image_tar"], remote_path="/root/")
        msg, err = ssh_exec(ssh, f"cat /root/{args['image_tar']} | docker load")
        logger.debug(f"stdout: {msg}")
        logger.debug(f"stderr: {err}")
    msg, err = ssh_exec(
        ssh, revapp_run.format(hostname=droplet.ip_address, image_name=args["image_name"])
    )
    logger.debug(f"stdout: {msg}")
    logger.debug(f"stderr: {err}")
    logger.info(f"Completed provisioning and starting of {droplet.name}")


def scp_progress(filename: str, size, sent) -> None:
    percent = sent / size * 100
    bar = int(percent // 10) * "=" + ">"
    print(f"{filename}: {percent:.2f}% |{bar}|")


def ssh_exec(ssh: SSHClient, cmd: str) -> Tuple[str, str]:
    """ use to get nicer output from SSHClient.exec_command """
    logger.debug(f"Executing '{cmd}'")
    _, stdout, stderr = ssh.exec_command(cmd)
    out_str: str = stdout.read().decode("utf-8").strip()
    err_str: str = stderr.read().decode("utf-8").strip()
    return out_str, err_str


def remove_droplet(mgr: Manager, name: Optional[str] = None, droplet: Optional[Droplet] = None):
    if droplet is None:
        if name:
            droplet = get_droplet(mgr, name)
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


def set_firewall(ctx_args):
    cmds = ["ufw allow in http", "ufw reject 2375/tcp", "ufw reject 2376/tcp"]


def str2path(ctx, param, value: str) -> Path:
    return Path(value) if value is not None else None


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


# Load all the CI env variables into the context obj for easy access
@click.group()
@click.option("--token", envvar="DO_TOKEN", required=True)
@click.option("--droplet-size", "size", envvar="DO_SIZE")
@click.option("--image-name", "image", envvar="IMAGE_NAME")
@click.option(
    "--ssh-key",
    type=click.Path(exists=True, dir_okay=False),
    callback=str2path,
    envvar="REVAPP_SSH_KEY",
)
@click.option(
    "--image-tar", type=click.Path(exists=True, dir_okay=False), envvar="CI_CACHE_IMAGE_FILE"
)
@click.option("--driver", help="specify the docker-machine driver e.g., virtualbox")
@click.pass_context
def app(ctx, **kwargs):
    ctx.obj["mgr"] = Manager(token=kwargs["token"])
    ctx.obj["args"] = kwargs.copy()
    # ssh_key is handled a little special
    if kwargs["ssh_key"]:
        del ctx.obj["args"]["ssh_key"]
        rsa_key = RSAKey.from_private_key(kwargs["ssh_key"].open())
        rsa_fingerprint = fingerprint_key(rsa_key.get_base64())
        ctx.obj["args"]["ssh_keys"] = [rsa_fingerprint]
        ctx.obj["args"]["pkey"] = rsa_key


@app.command(help="create a new droplet to run the review app")
@click.option("--name", "-n", envvar="CI_BUILD_REF_SLUG", callback=format_name, required=True)
@click.option(
    "--replace",
    envvar="REVAPP_REPLACE",
    type=click.BOOL,
    is_flag=True,
    help="replace existing review app, if any",
)
@click.pass_context
def create(ctx, name: str, replace: bool) -> None:
    """ creates a new droplet to run the review app """
    exists = get_droplet(ctx.obj["mgr"], name)
    if exists:
        logger.info(f"Found existing droplet with name {name}: id {exists.id}")
        if not replace:
            raise ValueError(f"Review app for {name} already exists. Remove it or use --replace")
        remove_droplet(ctx.obj["mgr"], name)

    droplet_args = default_create_args.copy()
    droplet_args["name"] = name
    droplet_args.update(
        {k: ctx.obj["args"][k] for k in REQUIRED_ARGS if ctx.obj["args"].get(k) is not None}
    )
    droplet_args.update({k: ctx.obj["args"][k] for k in OPTIONAL_ARGS if ctx.obj["args"].get(k)})
    logging.debug(f"creating droplet with args {json.dumps(droplet_args)}")
    droplet = Droplet(**droplet_args)
    breakpoint()
    droplet.create()

    while droplet.status is None or droplet.ip_address is None:
        time.sleep(5)
        try:
            droplet.load()
        except Exception as e:
            raise e
    logger.info(f"droplet {droplet.name} ready on {droplet.ip_address}")

    provision_droplet(droplet, ctx.obj["args"])


# this won't work wtf
@app.command(help="re-provision an existing review app")
@click.option("--name", "-n", callback=format_name, required=True)
@click.pass_context
def provision(ctx, name):
    logger.info(f"Re-provisioning name {name}")
    droplet = get_droplet(ctx.obj["mgr"], name)
    provision_droplet(droplet, ctx.obj["args"])


@app.command(help="get the status of review app by branch name")
@click.option("--name", "-n", envvar="CI_BUILD_REF_SLUG", callback=format_name, required=True)
@click.option("--json", "json_format", is_flag=True, help="output in json format")
@click.pass_context
def status(ctx, name: str, json_format: bool):
    droplet = get_droplet(ctx.obj["mgr"], name)
    if droplet is None:
        logger.error(f"No review app found named: {name}")
        if json_format:
            print("{}")
    else:
        if json_format:
            print(
                json.dumps(
                    {
                        "name": name,
                        "status": droplet.status,
                        "ip_address": droplet.ip_address,
                        "created_at": droplet.created_at,
                    }
                )
            )
        else:
            print(
                f"{name}: {droplet.status} @ {droplet.ip_address}, created at {droplet.created_at}"
            )


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
@click.option("--name", "-n", envvar="CI_BUILD_REF_SLUG", callback=format_name, required=True)
@click.pass_context
def remove(ctx, name: str) -> None:
    """ removes an existing review app droplet """
    remove_droplet(ctx.obj["mgr"], name)


if __name__ == "__main__":
    app(obj={})
