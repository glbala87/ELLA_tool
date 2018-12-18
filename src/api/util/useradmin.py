import bcrypt
import datetime
import binascii
import hashlib
import base64
import os
import re
import pytz
from sqlalchemy import desc
from sqlalchemy.orm import joinedload
from vardb.datamodel import user
from api import AuthenticationError
from api.config import config

# Helper functions
def generate_password():
    password = base64.b64encode(os.urandom(10))[-10:-2]
    # Avoid passwords that are difficult to decipher from handwritten text
    if set(password) & set("0oOIli1/+"):
        return generate_password()
    if not check_password_strength(password):
        return generate_password()
    password_hash = hash_password(password)
    return password, password_hash


def get_user(session, user_or_username):
    if isinstance(user_or_username, (str, unicode)):
        u = session.query(user.User).filter(user.User.username == user_or_username).one_or_none()
        if u is None:
            raise AuthenticationError("Invalid username {}".format(user_or_username))
        return u
    else:
        return user_or_username


# Password check functions


def password_expired(user_object):
    return user_object.password_expiry < datetime.datetime.now(pytz.utc)


def check_password_strength(password):
    if len(password) < config["user"]["auth"]["password_minimum_length"]:
        return False

    N = config["user"]["auth"]["password_num_match_groups"]
    n = sum(
        [re.match(p, password) is not None for p in config["user"]["auth"]["password_match_groups"]]
    )
    return n >= N


def check_password(password, password_hash):
    return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8"))


def authenticate_user(session, user_or_username, password):
    user_object = get_user(session, user_or_username)

    if not user_object.active:
        raise AuthenticationError(
            "User {} is inactive. Contact support to re-activate.".format(user_object.username)
        )

    if user_object.incorrect_logins >= 6:
        raise AuthenticationError(
            "Too many failed logins. User {} is locked. Contact support to unlock.".format(
                user_object.username
            )
        )

    if not check_password(password, user_object.password):
        user_object.incorrect_logins += 1
        session.commit()
        if user_object.incorrect_logins >= 6:
            raise AuthenticationError(
                "Invalid credentials. Too many failed logins. User {} has been locked. Contact support to unlock.".format(
                    user_object.username
                )
            )

        raise AuthenticationError("Invalid credentials")
    elif password_expired(user_object):
        raise AuthenticationError("Password expired. Please change password.")

    user_object.incorrect_logins = 0
    session.commit()
    return user_object


def hash_password(password):
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt())


def hash_token(token):
    return hashlib.sha256(token).hexdigest()


def get_usersession_by_token(session, token):
    hashed_token = hash_token(token)
    user_session = (
        session.query(user.UserSession)
        .options(joinedload("user"))
        .filter(user.UserSession.token == hashed_token)
        .one_or_none()
    )

    if (
        user_session is None
        or user_session.expires < datetime.datetime.now(pytz.utc)
        or user_session.logged_out is not None
    ):
        return None

    return user_session


def create_session(session, user_id):
    u = session.query(user.User).filter(user.User.id == user_id).one()

    # Store hashed token in database
    token = binascii.hexlify(os.urandom(32))
    hashed_token = hash_token(token)
    userSession = user.UserSession(
        token=hashed_token,
        user_id=user_id,
        issued=datetime.datetime.now(pytz.utc),
        expires=u.password_expiry,
    )
    session.add(userSession)
    session.commit()
    return token


def logout(userSession):
    userSession.logged_out = datetime.datetime.now(pytz.utc)


def logout_all(session, user_id):
    open_user_sessions = (
        session.query(user.UserSession)
        .filter(user.UserSession.user_id == user_id, user.UserSession.logged_out.is_(None))
        .all()
    )
    for user_session in open_user_sessions:
        logout(user_session)


def change_password(session, user_or_username, old_password, new_password, override=False):
    """
    Change password for user

    :param session: scoped_session object
    :param user_or_username: user or username, extract user if username is provided
    :param old_password: Existing password
    :param new_password: New password to set
    :param override: If this is True, then it is called from command line, and does not verify the old_password. It also sets the password as expired, so that it needs to be changed.
    """
    user_object = get_user(session, user_or_username)
    if user_object.incorrect_logins >= 6 and not override:
        raise AuthenticationError(
            "Too many failed logins. User {} is locked. Contact support to unlock.".format(
                user_object.username
            )
        )

    if not override and not check_password(old_password, user_object.password):
        raise AuthenticationError("Invalid credentials.")

    if not user_object.active and not override:
        raise AuthenticationError(
            "User is deactivated. Unable to change password. Contact support."
        )

    if not check_password_strength(new_password):
        raise AuthenticationError("Password doesn't follow password strength guidelines.")

    old_passwords = (
        session.query(user.UserOldPassword)
        .filter(user.UserOldPassword.user_id == user_object.id)
        .order_by(desc(user.UserOldPassword.expired))
        .limit(13)
        .all()
    )

    if check_password(new_password, user_object.password):
        raise AuthenticationError(
            "Password is equal to an old password. Choose a different password."
        )
    for old_pw in old_passwords:
        if check_password(new_password, old_pw.password):
            raise AuthenticationError(
                "Password is equal to an old password. Choose a different password."
            )

    session.add(user.UserOldPassword(user_id=user_object.id, password=user_object.password))
    logout_all(session, user_object.id)
    user_object.password = hash_password(new_password)
    if override:
        user_object.password_expiry = datetime.datetime(1970, 1, 1, tzinfo=pytz.utc)
    else:
        now = datetime.datetime.now(pytz.utc)
        # Set password expiry at 2AM UTC, to avoid password (and user sessions) expiring during the daytime
        user_object.password_expiry = (
            now.replace(hour=2, minute=0, second=0, microsecond=0)
            + datetime.timedelta(days=1)
            + datetime.timedelta(days=config["user"]["auth"]["password_expiry_days"])
        )

    user_object.incorrect_logins = 0

    session.commit()


def deactivate_user(session, user_or_username):
    user_object = get_user(session, user_or_username)
    user_object.active = False
    logout_all(session, user_object.id)
    session.commit()


def activate_user(session, user_or_username):
    user_object = get_user(session, user_or_username)
    user_object.active = True
    session.commit()


def add_user(session, username, first_name, last_name, email, group_id):
    """
    Add user with a generated password
    """

    existing_user = session.query(user.User).filter(user.User.username == username).one_or_none()

    assert existing_user is None, "Username {} already exists".format(username)

    existing_group = (
        session.query(user.UserGroup).filter(user.UserGroup.id == group_id).one_or_none()
    )

    assert existing_group is not None, "Usergroup with id {} does not exist".format(group_id)

    password, password_hash = generate_password()

    u = user.User(
        username=username,
        first_name=first_name,
        last_name=last_name,
        email=email,
        group_id=group_id,
        password=password_hash,
        password_expiry=datetime.datetime(1970, 1, 1, tzinfo=pytz.utc),
    )

    session.add(u)
    return u, password


def modify_user(session, user_or_username, **kwargs):
    user_object = get_user(session, user_or_username)
    for k, v in kwargs.items():
        setattr(user_object, k, v)
    return user_object
