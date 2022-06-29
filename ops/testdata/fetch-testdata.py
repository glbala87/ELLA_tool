#!/usr/bin/env python3
from __future__ import annotations

import argparse
import logging
from argparse import ArgumentParser
from enum import Enum
from pathlib import Path
from typing import Optional

from git import GitRef, RefType, Repository

###
### This script is meant to be run directly on a host, even if ELLA is running in a container.
### As such, we're using only standard library modules and not a more complete python git
### implementation.
###

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(Path(__file__).stem)

ROOT = Path(__file__).absolute().parents[2]
TESTDATA_FOLDER = ROOT / "ella-testdata"
ELLA_TESTDATA_URL_GIT = "git@gitlab.com:alleles/ella-testdata.git"
ELLA_TESTDATA_URL_HTTPS = "https://gitlab.com/alleles/ella-testdata.git"
DEFAULT_REF = GitRef(type=RefType.DEFAULT)


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
    status: bool
    reset: bool
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


def repo_status(repo: Repository):
    print("Repo:")
    print(f"    path:     {repo.repo_dir}")
    if not repo.repo_dir.exists():
        print(f"    exists:   {repo.repo_dir.exists()}")
        exit(1)
    print(f"    ref:      {repo.ref} ({repo.sha.ref})")
    print(f"    shallow:  {repo.is_shallow()}")
    print()
    print("Remote:")
    print(f"    url:      {repo.remote_url}")


def main():
    if args.mode is FetchModes.OFFLINE:
        remote_url = None
    elif args.mode is FetchModes.SSH:
        remote_url = ELLA_TESTDATA_URL_GIT
    elif args.mode is FetchModes.HTTPS:
        remote_url = ELLA_TESTDATA_URL_HTTPS
    else:
        remote_url = guess_url()

    data_repo = Repository(TESTDATA_FOLDER, remote_url, offline=args.mode is FetchModes.OFFLINE)

    if args.status:
        repo_status(data_repo)
        exit()
    elif args.reset:
        if data_repo.repo_dir.exists():
            data_repo.reset_repo(keep_dir=True)
        else:
            logger.info("Repo does not exist, skipping reset")

        if args.ref:
            logger.warning(
                f"If you want to reset to a specific ref, use --clean instead of --reset"
            )
        exit()

    # Get current branch name
    if args.ref:
        target_ref = data_repo.find_ref(args.ref)
    elif data_repo.git_dir.exists() and not args.clean:
        target_ref = data_repo.ref
    else:
        target_ref = DEFAULT_REF
    logger.debug(f"Using ref {target_ref}")

    if target_ref.type is RefType.NOT_FOUND:
        if not data_repo.repo_dir.exists():
            logger.error(
                f"Repo {data_repo.repo_dir} does not exist locally. If ref is a commit hash and not the HEAD of a branch, try again using --full"
            )
        raise ValueError(
            f"Ref '{args.ref}' is invalid. mode={args.mode}, remote_url={data_repo.remote_url}"
        )

    if args.clean or not data_repo.git_dir.exists():
        logger.info(f"Cloning new/overwriting existing test data")

        if args.full or target_ref.type is RefType.COMMIT:
            depth = None
        else:
            depth = 1

        data_repo.clone(target_ref, depth=depth, force=args.clean)
        logger.info(f"Successfully cloned testdata to ref {data_repo.ref} ({data_repo.sha})")
    elif data_repo.ref.matches(target_ref):
        data_repo.pull()
    else:
        data_repo.checkout(target_ref)

    repo_status(data_repo)


if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument("--status", action="store_true", help="Show status of local testdata repo")
    parser.add_argument("--reset", action="store_true", help="Remove contents in local repo dir")
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
