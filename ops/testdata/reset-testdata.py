import gzip
import logging
import os
from pathlib import Path
import requests
import subprocess
import sys

from cli.commands.database.make_db import make_db
from vardb.util.db import DB

logger = logging.getLogger(__file__)

ROOT = Path(__file__).parent.parent.parent.absolute()
TESTDATA_FOLDER = ROOT / "ella-testdata"
SPACES_CONFIG = {"bucket_name": "ella", "is_public": True, "region": "fra1"}


def remote_path(sha: str):
    return f"https://ella.fra1.digitaloceanspaces.com/testdata/{sha}/ella-testdata.psql.gz"


def get_sha():
    return (
        subprocess.check_output(f"git -C {TESTDATA_FOLDER} rev-parse --short HEAD".split())
        .decode()
        .strip("\n")
    )


def testdata_clean():
    r = subprocess.check_output(f"git -C {TESTDATA_FOLDER} status -s".split())
    return not bool(r)


def dump_exists(url: str):
    r = requests.head(url)
    return r.status_code < 400


def drop_db(remake: bool = False):
    db = DB()
    db.connect()

    db.engine.execute("DROP SCHEMA public CASCADE")  # type: ignore
    db.engine.execute("CREATE SCHEMA public")  # type: ignore

    if remake:
        make_db(db)
        db.session.commit()  # type: ignore

    db.disconnect()


def reset_from_dump(url: str):
    drop_db(remake=False)

    with requests.get(url) as r:
        p = subprocess.Popen(
            "psql -d postgres".split(), stdin=subprocess.PIPE, stdout=Path(os.devnull).open("w")
        )
        p.communicate(gzip.decompress(r.content))
        p.wait()


def reset(additional_arguments=None):
    logger.info(f"Resetting database from script")
    drop_db(remake=True)
    subprocess.check_call(
        f"python {TESTDATA_FOLDER}/testdata/deposit_testdata.py {'' if additional_arguments is None else additional_arguments}".split(),
        bufsize=0,
        stdout=sys.stdout,
    )


def main():
    if len(sys.argv) > 1:
        additional_arguments = " ".join(sys.argv[1:])
    else:
        additional_arguments = ""

    sha = get_sha()
    url = remote_path(sha)
    if additional_arguments:
        logger.info(
            f"Additional arguments provided ({additional_arguments}). Resetting with script."
        )
        reset(additional_arguments)
    elif not testdata_clean():
        logger.info(f"{TESTDATA_FOLDER} is not clean. Resetting with script.")
        reset()
    elif not dump_exists(url):
        logger.info(f"Dump for {sha} does not exist. Resetting with script.")
        reset()
    else:
        logger.info(f"Resetting database from dump {url}")
        reset_from_dump(url)
    logger.info("Database reset")


if __name__ == "__main__":
    main()
