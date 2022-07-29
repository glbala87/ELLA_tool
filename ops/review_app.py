#!/usr/bin/env python3

import datetime
import hashlib
import json
import logging
import logging.config
import os
import shutil
import time
from base64 import b64decode
from dataclasses import dataclass, field
from enum import Enum
from functools import wraps
from operator import itemgetter
from pathlib import Path
from socket import timeout as SocketTimeout
from typing import Dict, List, Mapping, Optional, Sequence, Tuple, Union, get_type_hints

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

###
### general settings
###

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
    "loggers": {
        logger_name: {"handlers": ["console"], "level": "INFO"},
        "paramiko": {"handlers": ["console"], "level": "WARN"},
    },
}
logging.config.dictConfig(log_config)
logger = logging.getLogger(logger_name)

###
### review app settings
###

OPS_DIR = Path(__file__).resolve().parent
REVAPP_START_SCRIPT = OPS_DIR / "start_review.sh"
LOCAL_REPO = Path("/local-repo")
if LOCAL_REPO.exists() and LOCAL_REPO.is_dir():
    REVAPP_BUILD_LOG = LOCAL_REPO / "build.log"
else:
    REVAPP_BUILD_LOG = Path("./build.log").resolve()


###
### digitalocean settings
###

DEFAULT_REGION = "fra1"
DEFAULT_SIZE = "s-1vcpu-2gb"
DEFAULT_DROPLET_IMAGE = "docker-20-04"
DEFAULT_TAG = "gitlab-review-app"

DROPLET_ATTRS = ("id", "name", "created_at", "status", "ip_address")
DROPLET_DETAILS = (
    ("region", ("name", "slug")),
    ("size", ("slug", "memory", "vcpus", "disk")),
    ("networks", False),
    ("features", False),
    ("image", ("id", "name", "slug", "distribution")),
)
DROPLET_PKGS = ("make",)

SCP_BAR_PERCENT = 0.05
SCP_BAR_PADDING = int(1 / SCP_BAR_PERCENT)
SSH_MAX_RETRIES = 3
SSH_DEFAULT_TIMEOUT = 60

# set up firewall on droplet to only listen on 22, 80 and 443
UFW_CONFIGS = list((OPS_DIR / "demo").glob("user*.rules"))
# expected output from correctly configured `ufw status`
UFW_STATUS_OK = """
Status: active

To                         Action      From
--                         ------      ----
22/tcp                     LIMIT       Anywhere
80/tcp                     ALLOW       Anywhere
443/tcp                    ALLOW       Anywhere
22/tcp (v6)                LIMIT       Anywhere (v6)
80/tcp (v6)                ALLOW       Anywhere (v6)
443/tcp (v6)               ALLOW       Anywhere (v6)
""".strip()

###
### support classes
###


class AppContext:
    mgr: Manager
    token: str


class RevappStatus(str, Enum):
    OK = "OK"
    ServerError = "ServerError / Loading"
    NotRunning = "Not Running"
    TimedOut = "Timed Out"
    Down = "Down"

    def __str__(self) -> str:
        return self.value


class RetriesExceeded(Exception):
    err_list: List[Exception] = []

    def __init__(self, max_retries: int, errors=[], msg: str = None, args=[], kwargs={}):
        if msg is not None:
            self.msg = msg.format(max_retries=max_retries, *args, **kwargs)
        else:
            self.msg = f"Command failed after exceeding {max_retries} retries"
        self.err_list = errors


class ExecFailed(Exception):
    rc: int
    host: str
    cmd: str
    stdout: str
    stderr: str
    msg: str

    def __init__(
        self, host: str, cmd: str, rc: int, stdout: str, stderr: str, msg: Optional[str] = None
    ):
        self.rc = rc
        self.cmd = cmd
        self.host = host
        self.stdout = stdout
        self.stderr = stderr
        if msg is None:
            msg = f"Received rc {self.rc} from {self.host} while running {self.cmd}: {self.stderr}"
        self.msg = msg


@dataclass
class ExecResponse:
    cmd: str
    host: str
    rc: int
    stdout: str
    stderr: str


@dataclass
class RevappEnviron:
    virtual_host: str
    demo_image: str
    demo_name: str
    demo_port: int = 3114
    demo_user: int = 1000
    demo_group: int = 1000
    demo_host_port: int = 80
    ella_branch: Optional[str] = None
    ref: Optional[str] = None
    _file: Path = field(init=False)

    def __post_init__(self) -> None:
        self._file = OPS_DIR / f"{self.demo_name}.env"

    def validate(self) -> Tuple[bool, List[str]]:
        empty_vars = [
            k for k, v in self.vars().items() if v is None and not is_optional_arg(self, k)
        ]
        return not empty_vars, empty_vars

    def vars(self):
        return {
            k: v if v is not None else "" for k, v in vars(self).items() if not k.startswith("_")
        }

    def write(self, *, export: bool = True):
        is_valid, empty_vars = self.validate()
        if not is_valid:
            raise ValueError(f"Missing values for: {', '.join(empty_vars)}")

        # if sourcing from shell script, export is good. if using as .env file, it's not
        if export:
            prefix = "export "
        else:
            prefix = ""

        with self._file.open("wt") as f:
            for k, v in self.vars().items():
                var_name = f"{prefix}{k.upper()}"
                var_value = str(v) if v is not None else ""
                if export and var_value:
                    var_value = f'"{var_value}"'
                var_value = f'"{v}"' if v is not None else ""
                f.write(f"{var_name}={var_value}\n")
        logger.info(f"Wrote env file to {self._file}")

    def upload(self, client: SCPClient, *, remote_path: Optional[str] = None):
        if remote_path is None:
            remote_path = self._file.name
        if self._file.exists():
            logger.info(f"Re-using existing env file {self._file}")
        else:
            self.write()
        if LOCAL_REPO.is_dir():
            # write copy to /local-repo for CI debugging
            shutil.copy(self._file, LOCAL_REPO / self._file.name)
        scp_put(client, file=self._file, remote_path=remote_path)
        logger.info(f"Uploaded env file to remote host")


###
### utility funcs
###


def is_optional_arg(obj, arg: str) -> bool:
    obj_types = get_type_hints(obj)
    if arg not in obj_types:
        raise ValueError(f"{arg} is not a valid argument for {obj}")
    return str(obj_types[arg]).startswith("typing.Union") and type(None) in obj_types[arg].__args__


def fingerprint_key(pubkey: str) -> str:
    """ generates the md5 hexdigest of the public key used by digitalocean """
    pub_digest = hashlib.md5(b64decode(pubkey.encode("utf-8"))).hexdigest()
    return ":".join([pub_digest[i : i + 2] for i in range(0, len(pub_digest), 2)])


def format_name(ctx, param, value: str) -> str:
    if not value.startswith("revapp-"):
        value = f"revapp-{value}"
    return value


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


def retry(
    catch_exc,
    max_retries: int = SSH_MAX_RETRIES,
    delay: int = 15,
    err_msg: Optional[str] = None,
):
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


###
### SSH funcs
###


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


def _get_transport(ssh: SSHClient):
    # this is always set after the client has connected, but checker still complains about Optional[Transport]
    t = ssh.get_transport()
    if t is None:
        raise AttributeError(f"SSHClient has no transport object")
    return t


@retry((SocketTimeout, PipeTimeout, ExecFailed), err_msg="SSH cmd '{1}' failed after {max_retries}")
def ssh_exec(
    ssh: SSHClient,
    cmd: str,
    check_rc: bool = True,
    timeout: int = SSH_DEFAULT_TIMEOUT,
    bufsize: int = -1,
):
    """ executes the command, returning formatted output and optionally checking success (default) """
    logger.debug(f"Executing '{cmd}'")

    # SSHClient.exec_command does not allow checking the return code from what was executed, so we
    # are basically duplicating that function and checking it ourselves
    chan = _get_transport(ssh).open_session()
    # set timeout for blocking operations
    chan.settimeout(timeout)
    chan.exec_command(cmd)

    resp = ExecResponse(
        host=_get_transport(ssh).sock.getpeername()[0],
        cmd=cmd,
        rc=chan.recv_exit_status(),
        stdout="\n".join([line.rstrip() for line in chan.makefile("r", bufsize).readlines()]),
        stderr="\n".join(
            [line.rstrip() for line in chan.makefile_stderr("r", bufsize).readlines()]
        ),
    )

    if check_rc and resp.rc:
        logger.error(json.dumps(vars(resp)))
        raise ExecFailed(**vars(resp))
    else:
        logger.debug(json.dumps(vars(resp)))
    return resp


###
### SCP funcs
###


def scp_progress(filename: str, size: int, sent: int) -> None:
    percent = sent / size
    bar = int(percent // SCP_BAR_PERCENT) * "=" + ">"
    print(f"{filename}: {percent*100:.2f}% |{bar: <{SCP_BAR_PADDING}}|", end="\r")


@retry(Exception)
def scp_put(
    scp: SCPClient, *, file: Optional[Path] = None, files: Optional[List[Path]] = None, **kwargs
):
    if bool(file) == bool(files):
        raise ValueError("Exactly one of file or files must be specified")

    if file:
        put_files = [str(file)]
    elif files:
        put_files = [str(f) for f in files]

    str_files = ", ".join(put_files)
    xfer_start = datetime.datetime.now()
    try:
        scp.put(put_files, **kwargs)
    except Exception as e:
        # TODO: narrow down what exceptions this might throw
        xfer_total = datetime.datetime.now() - xfer_start
        logger.error(f"Transfer of {str_files} failed after {xfer_total}")
        raise e
    xfer_total = datetime.datetime.now() - xfer_start
    logger.info(f"Finished uploading file(s) {str_files} after {xfer_total}")


###
### digitalocean funcs
###


def get_droplet(mgr: Manager, name: str, tag: str = DEFAULT_TAG) -> Optional[Droplet]:
    logger.debug(f"Fetching droplet named {name}")
    all_drops = list_droplets(mgr, tag)
    by_name = [d for d in all_drops if d.name == name]
    if len(by_name) == 0:
        logger.info(f"No droplet found with name {name}")
        return None
    elif len(by_name) > 1:
        raise ValueError(f"Found multiple droplets named: {name}")
    return by_name[0]


def list_droplets(mgr: Manager, tag: str = DEFAULT_TAG) -> Sequence[Droplet]:
    logger.debug(f"Fetching all droplets with tag {tag}")
    all_drops = mgr.get_all_droplets(tag_name=tag)
    return all_drops


def provision_droplet(droplet: Droplet, pkey: RSAKey, image_name: str):
    ssh = get_ssh_conn(droplet.ip_address, pkey)
    # TODO: add option to show progress bar, is too noisy for runner loggers
    # scp = SCPClient(ssh.get_transport(), progress=scp_progress)
    scp = SCPClient(ssh.get_transport())

    pkg_str = " ".join(DROPLET_PKGS)
    logger.debug(f"Installing packages: {pkg_str}")
    ssh_exec(ssh, f"apt-get update -qq && apt-get install {pkg_str} -y -qq")
    logger.info(f"Finished installing {len(DROPLET_PKGS)} packages")

    provision_ufw(ssh, scp)
    logger.info(f"{droplet.name} provisioned")
    revapp_launch(ssh, scp, droplet.ip_address, image_name)
    logger.info(f"Finished starting review app on droplet {droplet.name}")
    ssh.close()


def provision_ufw(ssh: SSHClient, scp: SCPClient):
    logger.debug(f"Checking ufw status")
    status_resp = ssh_exec(ssh, "ufw status")
    if status_resp.stdout == UFW_STATUS_OK:
        logger.info(f"ufw status ok, skipping")
        return

    logger.debug(f"moving current ufw configs")
    for ufw_conf in UFW_CONFIGS:
        ssh_exec(ssh, f"mv /etc/ufw/{ufw_conf.name} /etc/ufw/{ufw_conf.name}.old")
    scp_put(scp, files=UFW_CONFIGS, remote_path="/etc/ufw/")

    logger.debug(f"reloading ufw config")
    ssh_exec(ssh, "ufw reload")
    status_resp = ssh_exec(ssh, "ufw status")
    if status_resp.stdout == UFW_STATUS_OK:
        raise ValueError(f"ufw status not matching after update: {status_resp.stdout}")
    logger.info(f"ufw successfully configured")


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


def trim_droplet(drop: Droplet, detailed=False) -> Dict:
    new_drop = {a: getattr(drop, a) for a in DROPLET_ATTRS}
    if detailed:
        for (key, vals) in DROPLET_DETAILS:
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


###
### review app funcs
###


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


def revapp_launch(ssh: SSHClient, scp: SCPClient, hostname: str, image_name: str):
    # set up environment for REVAPP_START_SCRIPT
    logger.debug("Setting up environment file")
    revapp_env = RevappEnviron(
        demo_image=image_name,
        virtual_host=hostname,
        demo_name=os.getenv("DEMO_NAME", os.getenv("REVAPP_NAME", "revapp")),
        ella_branch=os.getenv("REVAPP_NAME"),
        ref=os.getenv("REVAPP_REF") or os.getenv("REF"),
    )
    revapp_env.write()
    # logger.debug(f"Using env: {revapp_env._file.read_text()}")
    revapp_env.upload(scp)

    # start script is what clones the repo, so needs to be uploaded even though it's not
    # modified during the build
    logger.debug("uploading start script")
    scp_put(scp, file=REVAPP_START_SCRIPT)

    logger.info("running start script")
    exec_cmd = f"./{REVAPP_START_SCRIPT.name}"
    if revapp_env.ella_branch:
        exec_cmd += f" {revapp_env.ella_branch}"
    # keep a build log for debugging on the droplet
    resp = ssh_exec(ssh, exec_cmd, timeout=300)
    if resp.rc:
        logger.warn(f"Got rc {resp.rc} on command {resp.cmd}")
        logger.warn(f"App may not have started correctly")
    REVAPP_BUILD_LOG.write_text(json.dumps(vars(resp), sort_keys=True, indent=4))
    logger.info(f"remote build log written to {REVAPP_BUILD_LOG}")

    logger.info(f"Review app started on http://{hostname}:{revapp_env.demo_host_port}")


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
@click.pass_obj
def app(ctx: AppContext, token: str, verbose: bool, debug: bool):
    if debug:
        logger.setLevel(logging.DEBUG)
    elif verbose:
        logger.setLevel(logging.INFO)
    ctx.token = token
    ctx.mgr = Manager(token=token)


@app.command(help="create a new droplet to run the review app")
@click.argument("name", envvar="REVAPP_NAME", callback=format_name)
@click.option(
    "--droplet-size",
    "size",
    envvar="REVAPP_SIZE",
    default=DEFAULT_SIZE,
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
    help="if found, destroy existing review app droplet and create a new one",
)
@click.pass_obj
def create(
    ctx: AppContext,
    name: str,
    size: str,
    image_name: str,
    ssh_key: RSAKey,
    replace: bool,
):
    """ creates a new droplet to run the review app """
    exists = get_droplet(ctx.mgr, name)
    if exists:
        logger.info(f"Found existing droplet with name {name}: id {exists.id}")
        if replace:
            remove_droplet(ctx.mgr, name)
            exists = None
        else:
            raise ValueError(f"Review app for {name} already exists. Remove it or use --replace")

    droplet_args = {
        "token": ctx.token,
        "name": name,
        "region": DEFAULT_REGION,
        "size": size,
        "image": DEFAULT_DROPLET_IMAGE,
        "tags": [DEFAULT_TAG],
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
@click.pass_obj
def reprovision(ctx: AppContext, name: str, image_name: str, ssh_key: RSAKey):
    # TODO: set timeout option on digitalocean side
    logger.info(f"Re-provisioning name {name}")
    droplet = get_droplet(ctx.mgr, name)
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
@click.pass_obj
def status(ctx: AppContext, name: str, json_format: bool, fields: List[str]):
    droplet = get_droplet(ctx.mgr, name)
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
@click.option("--sort", "sort_key", type=click.Choice(DROPLET_ATTRS, False), default="name")
@click.pass_obj
def list_apps(ctx: AppContext, json_format: bool, detailed: bool, sort_key: str):
    raw_droplets = list_droplets(ctx.mgr)
    trimmed = sorted([trim_droplet(d) for d in raw_droplets], key=itemgetter(sort_key))
    if not json_format and not detailed:
        print_table(trimmed, DROPLET_ATTRS)
    else:
        print(json.dumps(trimmed, indent=4))


@app.command(help="remove an existing review app droplet")
@click.argument("name", envvar="REVAPP_NAME", callback=format_name)
@click.pass_obj
def remove(ctx: AppContext, name: str):
    """ removes an existing review app droplet """
    remove_droplet(ctx.mgr, name)


if __name__ == "__main__":
    app(obj=AppContext())
