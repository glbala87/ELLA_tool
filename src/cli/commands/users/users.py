import base64
import click
import datetime
import pytz
import sys
import os
from copy import deepcopy
from functools import wraps

import bcrypt
from api.schemas.users import UserSchema
from api.util.useradmin import hash_password, change_password, deactivate_user, modify_user, check_password_strength, get_user
from vardb.datamodel import DB
from vardb.datamodel import user


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
def cmd_users_list():
    """
    List all users
    """
    db = DB()
    db.connect()
    session = db.session()
    users = session.query(user.User).all()

    header = {'id': 'id', 'username': 'username', 'first_name': 'first_name', 'last_name': 'last_name', 'password_expiry': 'password_expiry'}
    row_format = "{id:^10}| {username:<20} | {first_name:<30} | {last_name:<30} | {password_expiry:<30}"
    click.echo(row_format.format(**header))
    click.echo(row_format.format(
        **{'id': '-' * 10, 'username': '-' * 20, 'first_name': '-' * 30, 'last_name': '-' * 30, 'password': '-' * 60, 'password_expiry': '-' * 40}))
    for u in users:
        click.echo(row_format.format(**{h: encode(getattr(u,h)) for h in header}))


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

    existing_user = session.query(user.User).filter(
        user.User.username == username,
    ).one_or_none()

    assert existing_user is None, "Username %s already exists" % username

    group = session.query(user.UserGroup).filter(
        user.UserGroup.name == usergroup
    ).one()

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
    session.commit()

    click.echo("Added user {username} ({last_name}, {first_name}) with password {password}".format(
        username=username,
        first_name=first_name,
        last_name=last_name,
        password=password
    ))


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
        user.User.username == username
    ).one()

    click.echo("User {username} ({last_name}, {first_name}) has been modified: ".format(
        username=username,
        first_name=u_after.first_name,
        last_name=u_after.last_name,
    ))

    N_changes = 0
    for k in modified:
        from_val = encode(getattr(u_before, k))
        to_val = encode(getattr(u_after, k))
        if from_val != to_val:
            N_changes += 1
            click.echo("\t{key}: {from_val} ---> {to_val}".format(key=k, from_val=from_val, to_val=to_val))

    if N_changes == 0:
        click.echo("No modifications made!")



