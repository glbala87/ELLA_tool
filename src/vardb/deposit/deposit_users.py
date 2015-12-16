import json
import argparse
import logging

import vardb.datamodel
from vardb.datamodel import user

log = logging.getLogger(__name__)


def import_users(users):
    session = vardb.datamodel.Session()

    for u in users:
        new_user = user.User(**u)
        session.add(new_user)
        log.info("Adding user {}".format(u['username']))

    session.commit()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="""Adds new users from JSON file.""")
    parser.add_argument("--users", action="store", dest="userPath",
                        required=True, default=None,
                        help="Path to users JSON file")

    args = parser.parse_args()

    with open(args.userPath) as fd:
        users = json.load(fd)

    if not users:
        raise RuntimeError("No users found in file {}".format(args.userPath))

    import_users(users)
