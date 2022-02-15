from argparse import ArgumentParser
import shutil
import subprocess
from pathlib import Path
import sys
import logging

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__file__)

ROOT = Path(__file__).parent.parent.parent.absolute()
TESTDATA_FOLDER = ROOT / "ella-testdata"


try:
    ELLA_TESTDATA_URL = "git@gitlab.com:alleles/ella-testdata.git"
    subprocess.check_call(f"git ls-remote {ELLA_TESTDATA_URL} HEAD".split())
except:
    logger.info("Could not access repo over git+ssh. Falling back to https.")
    ELLA_TESTDATA_URL = "https://gitlab.com/alleles/ella-testdata"


def branch_exists_at_remote(branchname: str):
    try:
        subprocess.check_call(
            f"git ls-remote --exit-code {ELLA_TESTDATA_URL} refs/heads/{branchname}".split()
        )
        return True
    except:
        return False


def clone(branchname: str, full_clone: bool):
    subprocess.check_call(
        f"git -C {ROOT} clone --branch {branchname} {'' if full_clone else '--depth 1'} {ELLA_TESTDATA_URL}".split()
    )


def checkout_branch(branchname: str):
    subprocess.check_call(f"git -C {TESTDATA_FOLDER} checkout --detach {branchname}".split())


def main():
    parser = ArgumentParser()
    parser.add_argument(
        "-f", default=False, action="store_true", help="Remove testdata before refetching"
    )
    parser.add_argument("--tag", help="Specific tag, sha or branch to fetch")
    parser.add_argument("--full", default=False, action="store_true", help="Clone full repository")
    args = parser.parse_args()
    if args.f:
        if len(sys.argv) > 1 and sys.argv[1] == "-f" and TESTDATA_FOLDER.exists():
            shutil.rmtree(TESTDATA_FOLDER)

    # Get current branch name
    if args.tag is None:
        branchname = (
            subprocess.check_output("git rev-parse --abbrev-ref HEAD".split()).decode().strip("\n")
        )
    else:
        if not branch_exists_at_remote(args.tag):
            raise RuntimeError(f"Ref {args.tag} not found at remote")
        branchname = args.tag

    if not TESTDATA_FOLDER.exists():
        if branch_exists_at_remote(branchname):
            clone(branchname, args.full)
        else:
            clone("master", args.full)
    else:
        logger.info("Data already fetched. Nothing to do.")


if __name__ == "__main__":
    main()
