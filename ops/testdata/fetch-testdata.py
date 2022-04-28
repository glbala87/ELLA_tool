#!/usr/bin/env python3
from __future__ import annotations


import argparse
import logging
from argparse import ArgumentParser
from enum import Enum
from pathlib import Path
from typing import Optional

from git import Repository, RefType

logging.basicConfig(
    level=logging.DEBUG, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(Path(__file__).stem)
logging.getLogger("root").setLevel(logging.DEBUG)

DEFAULT_BRANCH = "master"
ROOT = Path(__file__).absolute().parents[2]
TESTDATA_FOLDER = ROOT / "ella-testdata"
ELLA_TESTDATA_URL_GIT = "git@gitlab.com:alleles/ella-testdata.git"
ELLA_TESTDATA_URL_HTTPS = "https://gitlab.com/alleles/ella-testdata"


class FetchModes(Enum):
    SSH = "ssh"
    HTTPS = "https"
    OFFLINE = "offline"
    AUTO = "auto"

    @classmethod
    def members(cls):
        return [m.value for m in cls.__members__.values()]

    @classmethod
    def metavar(cls):
        return "{" + ",".join(cls.members()) + "}"


class Args(argparse.Namespace):
    clean: bool
    ref: Optional[str]
    full: bool
    mode: FetchModes


def guess_url():
    if Repository(remote_url=ELLA_TESTDATA_URL_GIT).remote_ref_exists("HEAD"):
        return ELLA_TESTDATA_URL_GIT
    elif Repository(remote_url=ELLA_TESTDATA_URL_HTTPS).remote_ref_exists("HEAD"):
        logger.debug("Could not access repo with git protocol. Falling back to https.")
        return ELLA_TESTDATA_URL_HTTPS
    else:
        logger.warning(
            f"Unable to access git repo via {ELLA_TESTDATA_URL_GIT} or {ELLA_TESTDATA_URL_HTTPS}, continuing in offline mode"
        )


def main():
    if args.mode is FetchModes.OFFLINE:
        remote_url = None
    elif args.mode is FetchModes.SSH:
        remote_url = ELLA_TESTDATA_URL_HTTPS
    elif args.mode is FetchModes.HTTPS:
        remote_url = ELLA_TESTDATA_URL_GIT
    else:
        remote_url = guess_url()

    is_offline = remote_url is None
    data_repo = Repository(TESTDATA_FOLDER, remote_url)

    # Get current branch name
    detached = False
    if args.ref:
        ref_type = data_repo.ref_type(args.ref, offline=is_offline)
        if ref_type is RefType.NOT_FOUND:
            raise ValueError(
                f"Ref '{args.ref}' is invalid. offline_mode={args.offline}, remote_url={data_repo.remote_url}"
            )
        elif ref_type in [RefType.COMMIT, RefType.TAG]:
            detached = True
        target_ref = args.ref
    else:
        if data_repo.repo_dir.exists():
            target_ref = data_repo.ref
            ref_type = data_repo.ref_type(target_ref)
        else:
            target_ref = DEFAULT_BRANCH
            ref_type = RefType.BRANCH

    if args.full:
        depth = None
    else:
        depth = 1

    if not data_repo.git_dir.exists() or args.clean:
        if is_offline:
            logger.error(f"Cannot clone new data in offline mode")
            exit(1)
        logger.info(f"Cloning new/overwriting existing test data")
        data_repo.clone(branchname=target_ref, depth=depth, force=args.clean)
    else:
        if data_repo.ref != target_ref:
            logger.info(f"Switching from {data_repo.ref} to {target_ref}")
            if is_offline:
                logger.warning(f"Checking out new ref in offline mode, only using local worktree")
            data_repo.checkout(target_ref, detached=detached)
        elif not data_repo.is_shallow() and ref_type is RefType.BRANCH:
            if is_offline:
                logger.warning(
                    f"Running in offline mode, using existing data from ref {data_repo.ref}"
                )
            else:
                logger.info(f"Checking for new data in branch {target_ref}")
                data_repo.pull()
        else:
            logger.info("Data already fetched. Nothing to do.")


if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument(
        "--clean",
        default=False,
        action="store_true",
        help="Remove any existing testdata before cloning",
    )
    parser.add_argument("--ref", help="Specific tag, sha or branch to fetch")
    parser.add_argument("--full", action="store_true", help="Clone full repository")
    parser.add_argument(
        "--mode",
        type=FetchModes,
        metavar=FetchModes.metavar(),
        default=FetchModes.AUTO,
        help="Specify which protocol to use with git or offline to only use existing local data. Default: auto",
    )
    args = parser.parse_args(namespace=Args)

    main()
