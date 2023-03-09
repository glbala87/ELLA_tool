import argparse
import json
import logging
from typing import Dict, List

from sqlalchemy import or_

from api.config import config
from datalayer import filters
from vardb.datamodel import DB, annotationshadow, gene, user

log = logging.getLogger(__name__)


def import_groups(session, groups, log=log.info):
    # Store import_groups data (has to be inserted after groups)
    import_groups: Dict[str, List[str]] = dict()

    for g in groups:
        group_data = dict(g)
        group_name = group_data["name"]

        existing_group = (
            session.query(user.UserGroup)
            .filter(user.UserGroup.name == group_data["name"])
            .one_or_none()
        )

        db_official_genepanels = (
            session.query(gene.Genepanel)
            .filter(
                or_(
                    # If genepanel is specified with version, use that
                    filters.in_(
                        session,
                        (gene.Genepanel.name, gene.Genepanel.version),
                        [gp for gp in group_data["genepanels"] if len(gp) == 2],
                    ),
                    # Otherwise, pick all versions of a genepanel
                    filters.in_(
                        session,
                        gene.Genepanel.name,
                        [gp[0] for gp in group_data["genepanels"] if len(gp) == 1],
                    ),
                ),
                gene.Genepanel.official.is_(True),
            )
            .all()
        )

        for group_panel in group_data["genepanels"]:
            if len(group_panel) == 2:
                assert tuple(group_panel) in [
                    (gp.name, gp.version) for gp in db_official_genepanels
                ], f"Could not find genepanel {group_panel} in database"
            else:
                assert group_panel[0] in [
                    gp.name for gp in db_official_genepanels
                ], f"Could not find any genepanels named '{group_panel[0]}' in database"

        import_groups[group_name] = group_data.pop("import_groups", [group_name])

        if group_data.get("default_import_genepanel"):
            default_import_genepanel = group_data.pop("default_import_genepanel")

            # Use specified version if provided, otherwise, use latest version
            if len(default_import_genepanel) == 1:
                latest_version = (
                    session.query(gene.Genepanel.version)
                    .filter(
                        gene.Genepanel.name == default_import_genepanel[0],
                        gene.Genepanel.official.is_(True),
                    )
                    .order_by(gene.Genepanel.date_created.desc())
                    .scalar_all()[0]
                )
                default_import_genepanel = (default_import_genepanel[0], latest_version)

            assert tuple(default_import_genepanel) in [
                (gp.name, gp.version) for gp in db_official_genepanels
            ], f"Could not find genepanel {default_import_genepanel} in database"

            group_data["default_import_genepanel_name"] = default_import_genepanel[0]
            group_data["default_import_genepanel_version"] = default_import_genepanel[1]

        if not existing_group:
            group_data["genepanels"] = db_official_genepanels
            new_group = user.UserGroup(**group_data)
            session.add(new_group)
            log("Added user group {}".format(group_name))
        else:
            # Keep unofficial genepanels for group
            db_unofficial_genepanels = [
                gp for gp in existing_group.genepanels if gp.official is False
            ]
            group_data["genepanels"] = list(db_official_genepanels) + list(db_unofficial_genepanels)
            log("User group {} already exists, updating record...".format(group_data["name"]))
            for k, v in group_data.items():
                setattr(existing_group, k, v)

        # Check that usergroup's ACMG config is compatible with annotationshadowfrequency columns
        annotationshadow.check_usergroup_config(
            existing_group if existing_group else new_group, config
        )

    # Handle import_groups
    session.flush()
    usergroup_id_names = session.query(user.UserGroup.id, user.UserGroup.name).all()
    usergroup_name_id = {gn: gid for gid, gn in usergroup_id_names}
    for group_name, import_group_names in import_groups.items():
        # Delete all usergroupimport rows for this group before re-inserting new
        session.execute(
            user.UserGroupImport.delete().where(
                user.UserGroupImport.c.usergroup_id == usergroup_name_id[group_name]
            )
        )
        for import_group_name in import_group_names:
            session.execute(
                user.UserGroupImport.insert().values(
                    usergroup_id=usergroup_name_id[group_name],
                    usergroupimport_id=usergroup_name_id[import_group_name],
                )
            )

    session.commit()


def import_users(session, users):
    for u in users:
        existing_user = (
            session.query(user.User).filter(user.User.username == u["username"]).one_or_none()
        )

        if "group" not in u:
            raise RuntimeError("User {} is not in any group.".format(u["username"]))
        u["group"] = session.query(user.UserGroup).filter(user.UserGroup.name == u["group"]).one()

        if not existing_user:
            new_user = user.User(**u)
            session.add(new_user)
            log.info("Adding user {}".format(u["username"]))
        else:
            log.info("Username {} already exists, updating record...".format(u["username"]))
            for k, v in u.items():
                setattr(existing_user, k, v)

    session.commit()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="""Adds new users from JSON file.""")
    parser.add_argument(
        "--users", action="store", dest="users", required=False, help="Path to users JSON file"
    )
    parser.add_argument(
        "--groups", action="store", dest="groups", required=False, help="Path to groups JSON file"
    )

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
