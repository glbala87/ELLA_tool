import click
import sys
import json
from copy import deepcopy
from functools import wraps

from sqlalchemy.orm import joinedload
from sqlalchemy.orm.exc import NoResultFound

from api.util.useradmin import (
    change_password,
    deactivate_user,
    modify_user,
    get_user,
    generate_password,
    add_user,
)
from vardb.datamodel import DB
from vardb.datamodel import user
from vardb.deposit.deposit_users import import_groups


from cli.decorators import cli_logger, session


class UserGroupNotFound(NoResultFound):
    """Raised when a named user grouped can't be found in the database"""

    pass


# Decorators


def convert(join, *split_args):
    """
    Since click splits all options on whitespace, add this decorator before and after option decorators.

    Allows for whitespace in command line, e.g.

        ./cli foo --some_parameter_with_whitespace foo bar

    will pass argument some_parameter_with_whitespace as 'foo bar'

    Usage:
    @commandgroup.command("mycommand")
    @convert(True, "--some_parameter_with_whitespace")
    @options("--some_parameter_with_whitespace")
    @convert(False, "--some_parameter_with_whitespace")

    :param join: Boolean. Join or split arguments. Join and split arguments with '&'.
    :param split_args: Arguments to join/split on whitespace/&, e.g. --first_name
    :return:
    """
    if join:
        d = dict()
        k = None
        new_argv = []
        for arg in sys.argv:
            if arg.startswith("--"):
                if arg in split_args:
                    k = arg
                    d[k] = []
                    new_argv.append(k)
                    new_argv.append(None)
                    continue
                else:
                    new_argv.append(arg)
                    k = None
                    continue
            elif k is None:
                new_argv.append(arg)
                continue
            else:
                if new_argv[-1] is None:
                    new_argv[-1] = arg
                else:
                    new_argv[-1] += "&" + arg
        sys.argv = new_argv

    def _split(func):
        @wraps(func)
        def inner(*args, **kwargs):
            for k in kwargs:
                if "--" + k in split_args:
                    if kwargs[k] is not None:
                        kwargs[k] = " ".join(kwargs[k].split("&"))

            return func(*args, **kwargs)

        return inner

    return _split


# Helper functions


def encode(s):
    if isinstance(s, str):
        return s.encode("utf-8")
    else:
        return str(s)


def _user_exists(session, username):
    return session.query(user.User).filter(user.User.username == username).one_or_none() is not None


def _modify_user(session, username, echo_func, **kwargs):
    u = deepcopy(
        session.query(user.User)
        .options(joinedload("group"))
        .filter(user.User.username == username)
        .one()
    )

    if "new_username" in kwargs:
        kwargs["username"] = kwargs.pop("new_username")
    modified = {k: v for k, v in kwargs.items() if v is not None}

    u_mod = modify_user(session, username, **modified)

    n_changes = 0
    for k in modified:
        if k == "group_id":
            k = "usergroup"
            from_val = u.group.name
            to_val = u_mod.group.name
        else:
            from_val = encode(getattr(u, k))
            to_val = encode(getattr(u_mod, k))
        if from_val != to_val:
            n_changes += 1
            if n_changes == 1:
                echo_func(
                    "User {username} ({last_name}, {first_name}) has been modified: ".format(
                        username=username, first_name=u.first_name, last_name=u.last_name
                    )
                )
            echo_func(
                "\t{key}: {from_val} ---> {to_val}".format(key=k, from_val=from_val, to_val=to_val)
            )

    if n_changes == 0:
        echo_func(
            "No modifications made to {username} ({last_name}, {first_name}).".format(
                username=username, first_name=u.first_name, last_name=u.last_name
            )
        )

    return u_mod


def _add_user(session, echo_func, **kwargs):
    u, pw = add_user(
        session,
        kwargs["username"],
        kwargs["first_name"],
        kwargs["last_name"],
        kwargs.get("email"),
        kwargs["group_id"],
    )
    echo_func(
        "Added user {username} ({last_name}, {first_name}, {email}) with password {password}".format(
            username=u.username,
            first_name=u.first_name,
            last_name=u.last_name,
            email=u.email,
            password=pw,
        )
    )
    return u


# Commands


@click.group(help="User actions")
def users():
    pass


@users.command("list")
@click.option(
    "--group",
    multiple=True,
    help="Limit the display to users belonging to specific usergroups, multiple options allowed."
    + "If 'ALL' is given as option all users are displayed",
)
@click.option("--username", multiple=False, help="Display only a single user.")
@session
def cmd_users_list(session, group, username):
    accounts = None
    if username:
        accounts = session.query(user.User).filter(user.User.username == username).all()
    elif group and "ALL" not in group:
        accounts = (
            session.query(user.User)
            .join(user.UserGroup)
            .filter(user.UserGroup.name.in_(group))
            .all()
        )
    else:
        accounts = session.query(user.User).all()

    if not accounts:
        click.echo("No result")
        return

    header_user = {
        "id": "id",
        "username": "username",
        "first_name": "first_name",
        "last_name": "last_name",
        "password_expiry": "password_expiry",
    }
    header_user_genpanel = {"usergroup": "usergroup", "genepanels": "genepanels"}
    header = header_user.copy()
    header.update(header_user_genpanel)
    row_format = (
        "{id:^10}| {username:<20} | {first_name:<30} |"
        + "{last_name:<30} | {password_expiry:<30} | "
        + "{usergroup:<10} | {genepanels:<100}"
    )
    click.echo(row_format.format(**header))
    click.echo(
        row_format.format(
            **{
                "id": "-" * 10,
                "username": "-" * 20,
                "first_name": "-" * 30,
                "last_name": "-" * 30,
                "password": "-" * 60,
                "password_expiry": "-" * 40,
                "usergroup": "-" * 10,
                "genepanels": "-" * 20,
            }
        )
    )
    for a in accounts:
        d = {h: str(getattr(a, h)) for h in header_user}
        d.update(
            {
                "usergroup": a.group.name,
                "genepanels": ", ".join([p.name + "_" + p.version for p in a.group.genepanels]),
            }
        )
        click.echo(row_format.format(**d))


@users.command("activity")
@session
@cli_logger()  # Not logging output, just usage
def cmd_users_activity(logger, session):
    """
    List latest activity by users, sorted by last activity
    """
    usersessions = (
        session.query(user.UserSession).order_by(user.UserSession.lastactivity.desc()).all()
    )

    header = {
        "id": "id",
        "username": "username",
        "first_name": "first_name",
        "last_name": "last_name",
        "last_activity": "last_activity",
    }
    row_format = (
        "{id:^10}| {username:<20} | {first_name:<30} | {last_name:<30} | {last_activity:<35} |"
    )
    click.echo(row_format.format(**header))
    click.echo(
        row_format.format(
            id="-" * 10,
            username="-" * 20,
            first_name="-" * 30,
            last_name="-" * 30,
            last_activity="-" * 35,
        )
    )

    for u in usersessions:
        click.echo(
            row_format.format(
                id=u.user.id,
                username=u.user.username,
                first_name=u.user.first_name,
                last_name=u.user.last_name,
                last_activity=str(u.lastactivity),
            )
        )


@users.command("add_many", help="Import users from a json file")
@click.argument("json_file")
@click.option(
    "--group",
    multiple=True,
    help="Limit the import to users belonging to specific usergroups, multiple options allowed."
    + "If not given, all users are imported",
)
@click.option("-dry", is_flag=True, help="List users that would be imported")
@session
@cli_logger()
def cmd_add_many_users(
    logger, session, json_file, group, dry
):  # group is a tuple of names given as --group options
    from functools import partial

    users = json.load(open(json_file, "r"))

    def is_usergroup_configured_to_be_imported(group_names, user):
        return (
            user["group"]
            and user["group"].strip()
            and group_names
            and user["group"].strip().lower() in [s.strip().lower() for s in group_names]
        )

    filtered_users = (
        users
        if not group
        else list(filter(partial(is_usergroup_configured_to_be_imported, group), users))
    )

    for u in filtered_users:
        u["group_id"] = (
            session.query(user.UserGroup.id).filter(user.UserGroup.name == u.pop("group")).one()[0]
        )
        if _user_exists(session, u["username"]):
            u = _modify_user(session, u.pop("username"), logger.echo, **u)
        else:
            u = _add_user(session, logger.echo, **u)

    if dry:
        logger.echo("!!! DRY RUN: Rolling back changes")
        session.rollback()
    else:
        session.commit()
        logger.echo("Users added successfully")


@users.command("add_groups", help="Import user groups from a json file")
@click.argument("json_file")
@click.option(
    "--name",
    multiple=True,
    help="Limit the import to these groups, multiple options allowed."
    + " If not set, imports all groups.",
)
@click.option("-dry", is_flag=True, help="List groups that would be imported")
@session
@cli_logger()
def cmd_add_many_groups(
    logger, session, json_file, name, dry
):  # name is a tuple of names given as --name options
    from functools import partial

    groups = json.load(open(json_file, "r"))

    def is_usergroup_configured_to_be_imported(group_filter, group):
        return (
            group["name"]
            and group["name"].strip()
            and group_filter
            and group["name"].strip().lower() in [s.strip().lower() for s in group_filter]
        )

    filtered_groups = (
        groups
        if not name
        else list(filter(partial(is_usergroup_configured_to_be_imported, name), groups))
    )
    if dry:
        for g in filtered_groups:
            logger.echo("Would add group '{name}'".format(name=g["name"]))
        return

    import_groups(session, filtered_groups, log=logger.echo)


@users.command("reset_password")
@click.argument("username")
@session
@cli_logger()
def cmd_reset_password(logger, session, username):
    """
    Reset password for user (new password generated)
    """
    password, _ = generate_password()
    change_password(session, username, None, password, override=True)
    u = session.query(user.User).filter(user.User.username == username).one()

    click.echo(
        "Reset password for user {username} ({last_name}, {first_name}) with password {password}".format(
            username=username, first_name=u.first_name, last_name=u.last_name, password=password
        )
    )
    logger.echo(
        "Reset password for user {username} ({last_name}, {first_name}) with password *********".format(
            username=username, first_name=u.first_name, last_name=u.last_name
        ),
        db_only=True,
    )


@users.command("lock")
@click.argument("username")
@session
@cli_logger(prompt_reason=True)
def cmd_invalidate_user(logger, session, username):
    """
    Invalidate a user and all sessions.

    TODO: Add possibility to delete user, but only allow if user is not associated with any assessments or interpretations
    """

    u = get_user(session, username)
    deactivate_user(session, u)

    logger.echo(
        "User {username} ({last_name}, {first_name}) has been deactivated".format(
            username=username, first_name=u.first_name, last_name=u.last_name
        )
    )


@users.command("modify")
@convert(True, "--first_name", "--last_name")
@click.argument("username")
@click.option("--new_username")
@click.option("--first_name")
@click.option("--last_name")
@click.option("--email")
@click.option("--user_group")
@convert(False, "--first_name", "--last_name")
@session
@cli_logger()
def cmd_modify_user(logger, session, username, **kwargs):
    """
    Example: .. users modify --first_name Lars Marius -- lmarius\n
    The -- marks when a new parameter starts
    """

    answer = input(
        "Are you sure you want to modify user with command line arguments? If not, consider using the 'add_many' command to import with json-file. Type 'y' to confirm."
    )

    if answer != "y":
        logger.echo("Aborting")

    if "user_group" in kwargs:
        kwargs["group_id"] = (
            session.query(user.UserGroup.id)
            .filter(user.UserGroup.name == kwargs.pop("user_group"))
            .scalar()
        )

    _modify_user(session, username, logger.echo, **kwargs)
    logger.echo("User {} modified".format(username))
    session.commit()
