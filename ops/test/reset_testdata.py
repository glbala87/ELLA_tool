#!/usr/bin/env python

"""
We don't add this script to CLI as it's not considered
safe with regards to production.
"""


if __name__ == "__main__":

    import os
    import sys

    from applogger import setup_logger

    setup_logger()
    from vardb.util import DB
    from vardb.deposit.deposit_testdata import DepositTestdata
    from cli.commands.database.drop_db import drop_db
    from cli.commands.database.make_db import make_db

    if os.environ.get("PRODUCTION", "").lower() not in ["false", "0"]:
        print(
            "This script cannot be run in an production environment. Set env PRODUCTION=false to continue."
        )
        sys.exit(1)

    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--testset",
        action="store",
        dest="testset",
        help="Name of testset to import",
        default="default",
    )

    args = parser.parse_args()

    db = DB()
    db.connect()

    drop_db(db)
    make_db(db)

    dt = DepositTestdata(db)
    dt.deposit_all(test_set=args.testset)
