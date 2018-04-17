import base64
import click
import datetime
import pytz
import sys
import os
import json
from copy import deepcopy
from functools import wraps

import bcrypt
from sqlalchemy.orm.exc import NoResultFound

from api.schemas.users import UserSchema
from api.util.useradmin import hash_password, change_password, deactivate_user, modify_user, check_password_strength, get_user
from vardb.datamodel import DB
from vardb.datamodel import user
from vardb.deposit.deposit_users import import_groups


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

def generate_password():
    password = base64.b64encode(os.urandom(10))[-10:-2]
    if not check_password_strength(password):
        return generate_password()
    password_hash = hash_password(password)
    return password, password_hash


def encode(s):
    if isinstance(s, (str, unicode)):
        return s.encode('utf-8')
    else:
        return str(s)


# Commands

@click.group(help='User actions')
def users():
    pass


@users.command('list')
@click.option('--group', multiple=True, help="Limit the display to users belonging to specific usergroups, multiple options allowed." \
                + "If 'ALL' is given as option all users are displayed")
@click.option('--username', multiple=False, help="Display only a single user.")
def cmd_users_list(group, username):
    db = DB()
    db.connect()
    session = db.session()
    accounts = None
    if username:
        accounts = session.query(user.User).filter(user.User.username == username).all()
    elif group and 'ALL' not in group:
        accounts = session.query(user.User).\
            join(user.UserGroup).\
            filter(user.UserGroup.name.in_(group)).all()
    else:
        accounts = session.query(user.User).all()

    if not accounts:
        click.echo('No result')
        return

    header_user = {'id': 'id', 'username': 'username', 'first_name': 'first_name',
                   'last_name': 'last_name', 'password_expiry': 'password_expiry'
                  }
    header_user_genpanel = {'usergroup': 'usergroup', 'genepanels': 'genepanels'}
    header = header_user.copy()
    header.update(header_user_genpanel)
    row_format = "{id:^10}| {username:<20} | {first_name:<30} |" + \
                 "{last_name:<30} | {password_expiry:<30} | " + \
                 "{usergroup:<10} | {genepanels:<100}"
    click.echo(row_format.format(**header))
    click.echo(row_format.format(
        **{'id': '-' * 10, 'username': '-' * 20, 'first_name': '-' * 30,
           'last_name': '-' * 30, 'password': '-' * 60, 'password_expiry': '-' * 40,
           'usergroup': '-' * 10, 'genepanels': '-' * 20}))
    for a in accounts:
        d = {h: encode(getattr(a, h)) for h in header_user}
        d.update({'usergroup': a.group.name,
                  'genepanels': ", ".join([p.name + '_' + p.version for p in a.group.genepanels])})
        click.echo(row_format.format(**d))


@users.command('activity')
def cmd_users_activity():
    """
    List latest activity by users, sorted by last activity
    """

    db = DB()
    db.connect()
    session = db.session()
    usersessions = session.query(user.UserSession).order_by(user.UserSession.lastactivity.desc()).all()

    header = {'id': 'id', 'username': 'username', 'first_name': 'first_name', 'last_name': 'last_name', 'last_activity': 'last_activity'}
    row_format = "{id:^10}| {username:<20} | {first_name:<30} | {last_name:<30} | {last_activity:<35} |"
    click.echo(row_format.format(**header))
    click.echo(row_format.format(id='-'*10, username='-'*20, first_name='-'*30, last_name='-'*30, last_activity='-'*35))

    for u in usersessions:
        click.echo(row_format.format(id=u.user.id, username=u.user.username, first_name=u.user.first_name, last_name=u.user.last_name, last_activity=str(u.lastactivity)))


def _add_user(session, username, first_name, last_name, usergroup):
    """
    Add user with a generated password
    """

    existing_user = session.query(user.User).filter(
        user.User.username == username,
    ).one_or_none()

    assert existing_user is None, "Username %s already exists" % username

    try:
        group = session.query(user.UserGroup).filter(
            user.UserGroup.name == usergroup
        ).one()
    except NoResultFound, e:
        raise UserGroupNotFound("The user group '{}' was not found for user {}".format(usergroup, username), e)

    password, password_hash = generate_password()

    u = user.User(
        username=username,
        first_name=first_name,
        last_name=last_name,
        group_id=group.id,
        password=password_hash,
        password_expiry=datetime.datetime(1970,1,1,tzinfo=pytz.utc)
    )

    session.add(u)
    return u, password


@users.command('add')
@convert(True, "--first_name", "--last_name")
@click.option('--username')
@click.option('--first_name')
@click.option('--last_name')
@click.option('--usergroup')
@convert(False, "--first_name", "--last_name")
def cmd_add_user(username, first_name, last_name, usergroup):
    """
    Add user with a generated password
    """
    db = DB()
    db.connect()
    session = db.session()

    u, pw = _add_user(session, username, first_name, last_name, usergroup)
    session.commit()

    click.echo(u"Added user {username} ({last_name}, {first_name}) with password {password}".format(
        username=u.username,
        first_name=u.first_name,
        last_name=u.last_name,
        password=pw
    ))


@users.command('add_many', help="Import users from a json file")
@click.argument("json_file")
@click.option('--group', multiple=True, help="Limit the import to users belonging to specific usergroups, multiple options allowed." \
                + "If 'ALL' is given as option all users are imported")
@click.option('-dry', is_flag=True, help="List users that would be imported")
def cmd_add_many_users(json_file, group, dry):  # group is a tuple of names given as --group options
    from functools import partial
    users = json.load(open(json_file, 'r'))

    def is_usergroup_configured_to_be_imported(group_names, user):
        return user["group"] \
               and user["group"].strip() \
               and group_names \
               and user["group"].strip().lower() in map(lambda s: s.strip().lower(), group_names)

    filtered_users = users if 'ALL' in group else filter(partial(is_usergroup_configured_to_be_imported, group), users)

    if dry:
        for u in filtered_users:
            click.echo(u"Would add user '{username}' ('{last_name}', '{first_name}') from '{usergroup}')".format(
                username=u["username"],
                first_name=u["first_name"],
                last_name=u["last_name"],
                usergroup=u["group"]
            ))
        return

    db = DB()
    db.connect()
    session = db.session()

    for u in filtered_users:
        try:
            u, pw = _add_user(session, u["username"], u["first_name"], u["last_name"], u["group"])
        except (AssertionError, UserGroupNotFound) as e:
            print e
            continue
        click.echo(u"Added user {username} ({last_name}, {first_name}) with password {password}".format(
            username=u.username,
            first_name=u.first_name,
            last_name=u.last_name,
            password=pw
        ))
    session.commit()

@users.command('add_groups', help="Import user groups from a json file")
@click.argument("json_file")
@click.option('--name',  multiple=True, help="Limit the import to these groups, multiple options allowed."
              + " Value 'ALL' imports all groups.")
@click.option('-dry', is_flag=True, help="List groups that would be imported")
def cmd_add_many_groups(json_file, name, dry):  # name is a tuple of names given as --name options
    from functools import partial

    groups = json.load(open(json_file, 'r'))

    def is_usergroup_configured_to_be_imported(group_filter, group):
        return group["name"] \
               and group["name"].strip() \
               and group_filter \
               and group["name"].strip().lower() in map(lambda s: s.strip().lower(), group_filter)

    filtered_groups = groups if 'ALL' in name else filter(partial(is_usergroup_configured_to_be_imported, name), groups)
    if dry:
        for g in filtered_groups:
            click.echo(u"Would add group '{name}'".format(name=g["name"]))
        return

    db = DB()
    db.connect()
    session = db.session()

    import_groups(session, filtered_groups, log=click.echo)


@users.command('reset_password')
@click.argument("username")
def cmd_reset_password(username):
    """
    Reset password for user (new password generated)
    """
    db = DB()
    db.connect()
    session = db.session()

    password, _ = generate_password()
    change_password(session, username, None, password, override=True)
    u = session.query(user.User).filter(
        user.User.username == username
    ).one()

    click.echo("Reset password for user {username} ({last_name}, {first_name}) with password {password}".format(
        username=username,
        first_name=u.first_name.encode('utf-8'),
        last_name=u.last_name.encode('utf-8'),
        password=password
    ))


@users.command("lock")
@click.argument("username")
def cmd_invalidate_user(username):
    """
    Invalidate a user and all sessions.
    
    TODO: Add possibility to delete user, but only allow if user is not associated with any assessments or interpretations
    """

    db = DB()
    db.connect()
    session = db.session()
    u = get_user(session, username)
    deactivate_user(session, u)

    click.echo("User {username} ({last_name}, {first_name}) has been deactivated".format(
        username=username,
        first_name=u.first_name,
        last_name=u.last_name,
    ))


@users.command("modify")
@convert(True, "--first_name", "--last_name")
@click.argument("username")
@click.option("--new_username")
@click.option("--first_name")
@click.option("--last_name")
#@click.option("--user_role")
#@click.option("--user_group")
@convert(False, "--first_name", "--last_name")
def cmd_modify_user(username, **kwargs):
    """
    Example: .. users modify --first_name Lars Marius -- lmarius\n
    The -- marks when a new parameter starts
    """
    db = DB()
    db.connect()
    session = db.session()

    u_before = deepcopy(session.query(user.User).filter(
        user.User.username == username
    ).one())

    kwargs["username"] = kwargs.pop("new_username")
    modified = {k: v for k,v in kwargs.iteritems() if v is not None}

    modify_user(session, username, **modified)

    u_after = session.query(user.User).filter(
            # user.User.username == username
        user.User.username == modified['username'] if 'username' in modified else username
    ).one()

    click.echo("User {username} ({last_name}, {first_name}) has been modified: ".format(
        username=username,
        first_name=u_before.first_name,
        last_name=u_before.last_name,
    ))

    n_changes = 0
    for k in modified:
        from_val = encode(getattr(u_before, k))
        to_val = encode(getattr(u_after, k))
        if from_val != to_val:
            n_changes += 1
            click.echo("\t{key}: {from_val} ---> {to_val}".format(key=k, from_val=from_val, to_val=to_val))

    if n_changes == 0:
        click.echo("No modifications made!")



