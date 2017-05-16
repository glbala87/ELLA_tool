import json
import argparse
import logging
from sqlalchemy import tuple_
from sqlalchemy.orm.exc import NoResultFound

import vardb.datamodel
from vardb.datamodel import DB, user, gene

log = logging.getLogger(__name__)


def import_groups(session, groups):
    for g in groups:
        existing_group = session.query(user.UserGroup).filter(
            user.UserGroup.name == g['name']
        ).one_or_none()

        db_genepanels = session.query(gene.Genepanel).filter(
            tuple_(gene.Genepanel.name, gene.Genepanel.version).in_(g['genepanels'])
        ).all()

        if len(db_genepanels) != len(g['genepanels']):
            not_found = set(tuple(gp) for gp in g['genepanels'])-set((gp.name, gp.version,) for gp in db_genepanels)
            raise NoResultFound("Unable to find all genepanels in database: %s" %str(list(not_found)))

        g["genepanels"] = db_genepanels

        if not existing_group:
            new_group = user.UserGroup(**g)
            session.add(new_group)
            log.info("Adding user group {}".format(g['name']))
        else:
            log.info("User group {} already exists, updating record...".format(g['name']))
            for k, v in g.iteritems():
                setattr(existing_group, k, v)

    session.commit()


def import_users(session, users):

    for u in users:
        existing_user = session.query(user.User).filter(
            user.User.username == u['username']
        ).all()

        if 'group' not in u:
            raise RuntimeError("User {} is not in any group.".format(u['username']))
        group = session.query(user.UserGroup).filter(
            user.UserGroup.name == u["group"]
        ).one()
        u["group_id"] = group.id
        u.pop("group")

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
    parser.add_argument("--users", action="store", dest="users", required=False, help="Path to users JSON file")
    parser.add_argument("--groups", action="store", dest="groups", required=False, help="Path to groups JSON file")

    args = parser.parse_args()

    if not args.users and not args.groups:
        raise RuntimeError("You must specify either --users or --groups")

    if args.users:
        with open(args.users) as fd:
            users = json.load(fd)

    if args.groups:
        with open(args.groups) as fd:
            groups = json.load(fd)

    db = DB()
    db.connect()

    # User can reference group, so we need to import groups first
    if groups:
        import_groups(db.session, groups)
    if users:
        import_users(db.session, users)
