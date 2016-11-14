import json
import argparse
import logging

import vardb.datamodel
from vardb.datamodel import DB, user

log = logging.getLogger(__name__)


def import_users(session, users):

    for u in users:
        existing_user = session.query(user.User).filter(
            user.User.username == u['username']
        ).all()
        if not existing_user:
            new_user = user.User(**u)
            session.add(new_user)
            log.info("Adding user {}".format(u['username']))
        else:
            existing_user = existing_user[0]
            log.info("Username {} already exists, updating record...".format(u['username']))
            for k, v in u.iteritems():
                setattr(existing_user, k, v)

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

    db = DB()
    db.connect()

    import_users(db.session, users)
