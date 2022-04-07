#!/usr/bin/env python3

import argparse
import logging
from argparse import ArgumentParser
from pathlib import Path
from typing import Optional

from git import Repository, RefType

logging.basicConfig(
    level=logging.DEBUG, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)
logging.getLogger("root").setLevel(logging.DEBUG)

DEFAULT_BRANCH = "master"
ROOT = Path(__file__).absolute().parents[2]
TESTDATA_FOLDER = ROOT / "ella-testdata"
ELLA_TESTDATA_URL_GIT = "git@gitlab.com:alleles/ella-testdata.git"
ELLA_TESTDATA_URL_HTTPS = "https://gitlab.com/alleles/ella-testdata"


class Args(argparse.Namespace):
    clean: bool
    ref: Optional[str]
    full: bool


def main(repo_dir: Path, remote_url: str):
    parser = ArgumentParser()
    parser.add_argument(
        "--clean",
        default=False,
        action="store_true",
        help="Remove any existing testdata before cloning",
    )
    parser.add_argument("--ref", help="Specific tag, sha or branch to fetch")
    parser.add_argument("--full", default=False, action="store_true", help="Clone full repository")
    args = parser.parse_args(namespace=Args)
    data_repo = Repository(repo_dir, remote_url)

    # Get current branch name
    detached = False
    if args.ref:
        ref_type = data_repo.ref_type(args.ref)
        if ref_type is RefType.NOT_FOUND:
            raise ValueError(
                f"Ref '{args.ref}' is invalid / not found at remote {data_repo.remote_url}"
            )
        elif ref_type in [RefType.COMMIT, RefType.TAG]:
            detached = True
        target_ref = args.ref
    else:
        if data_repo.repo_dir.exists():
            target_ref = data_repo.ref
        else:
            target_ref = DEFAULT_BRANCH
        ref_type = data_repo.ref_type(target_ref)

    if args.full:
        depth = None
    else:
        depth = 1

    if not data_repo.repo_dir.exists() or args.clean:
        logger.info(f"Cloning new/overwriting existing test data")
        data_repo.clone(branchname=target_ref, depth=depth, force=args.clean)
    else:
        if data_repo.ref != target_ref:
            logger.info(f"Switching from {data_repo.ref} to {target_ref}")
            data_repo.checkout(target_ref, detached=detached)
        elif not data_repo.is_shallow() and ref_type is RefType.BRANCH:
            logger.info(f"Checking for new data in branch {target_ref}")
            data_repo.pull()
        else:
            logger.info("Data already fetched. Nothing to do.")


if __name__ == "__main__":
    if Repository(remote_url=ELLA_TESTDATA_URL_GIT).remote_ref_exists("HEAD"):
        testdata_remote = ELLA_TESTDATA_URL_GIT
    elif Repository(remote_url=ELLA_TESTDATA_URL_HTTPS).remote_ref_exists("HEAD"):
        logger.info("Could not access repo with git protocol. Falling back to https.")
        testdata_remote = ELLA_TESTDATA_URL_HTTPS
    else:
        raise RuntimeError(
            f"Unable to access git repo via {ELLA_TESTDATA_URL_GIT} or {ELLA_TESTDATA_URL_HTTPS}"
        )
    main(repo_dir=TESTDATA_FOLDER, remote_url=testdata_remote)
