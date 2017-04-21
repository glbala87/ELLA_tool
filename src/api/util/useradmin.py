from sqlalchemy import desc
import bcrypt
import datetime
import uuid
import re
from vardb.datamodel import user
from api import AuthenticationError
from api.config import config

# Helper functions

def get_user(session, user_or_username):
    if isinstance(user_or_username, (str, unicode)):
        u = session.query(user.User).filter(
            user.User.username == user_or_username
        ).one_or_none()
        if u is None:
            raise AuthenticationError("Invalid credentials")
        return u
    else:
        return user_or_username

# Password check functions
def password_expired(user_object):
    return user_object.password_expiry < datetime.datetime.now()


def check_password_strength(password):
    if len(password) < config["users"]["password_minimum_length"]:
        return False

    N = config["users"]["password_num_match_groups"]
    n = sum([re.match(p, password) is not None for p in config["users"]["password_match_groups"]])
    return n >= N


def check_password(password, password_hash):
    return bcrypt.checkpw(password.encode('utf-8'), password_hash.encode('utf-8'))


def authenticate_user(session, user_or_username, password, verify_not_expired=False):
    user_object = get_user(session, user_or_username)
    if user_object.incorrect_logins >= 6:
        raise AuthenticationError("Invalid credentials. Too many failed logins. User {} is locked. Contact support to unlock.".format(user_object.username))

    if not check_password(password, user_object.password):
        user_object.incorrect_logins += 1
        session.commit()
        if user_object.incorrect_logins >= 6:
            lock_user(session, user_object)
            raise AuthenticationError("Invalid credentials. Too many failed logins. User {} has been locked. Contact support to unlock.".format(user_object.username))

        raise AuthenticationError("Invalid credentials")
    elif password_expired(user_object) and verify_not_expired:
        raise AuthenticationError("Password expired", 403)

    user_object.incorrect_logins = 0
    session.commit()
    return user_object

def hash_password(password):
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt())


# Utility functions

def create_session(session, user_id):
    token = str(uuid.uuid1())
    u = session.query(user.User).filter(
        user.User.id == user_id,
    ).one()

    userSession = user.UserSession(
        token=token,
        user_id=user_id,
        issued=datetime.datetime.now(),
        expires=u.password_expiry,
    )
    session.add(userSession)
    session.commit()
    return userSession


def logout(userSession):
    userSession.expired = datetime.datetime.now()

def logout_all(session, user_id):
    open_user_sessions = session.query(user.UserSession).filter(
        user.UserSession.user_id == user_id,
        user.UserSession.expired.is_(None),
    ).all()
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

    if not override and not check_password(old_password, user_object.password):
        raise AuthenticationError("Invalid credentials.")

    if user_object.locked and not override:
        raise AuthenticationError("User is locked. Unable to change password. Contact support.")

    if not check_password_strength(new_password):
        raise AuthenticationError("Password doesn't follow password strength guidelines.", 403)

    old_passwords = session.query(user.UserOldPassword).filter(
        user.UserOldPassword.user_id == user_object.id
    ).order_by(
        desc(user.UserOldPassword.expired)
    ).limit(
        13
    ).all()


    if check_password(new_password, user_object.password):
        raise AuthenticationError("Password is equal to an old password. Choose a different password.")
    for old_pw in old_passwords:
        if check_password(new_password, old_pw.password):
            raise AuthenticationError("Password is equal to an old password. Choose a different password.")

    session.add(user.UserOldPassword(
        user_id=user_object.id,
        password=user_object.password
    ))
    logout_all(session, user_object.id)
    user_object.password = hash_password(new_password)
    if override:
        user_object.password_expiry = datetime.datetime.fromtimestamp(0)
    else:
        user_object.password_expiry = datetime.datetime.now()+datetime.timedelta(days=config["users"]["password_expiry_days"])

    if override:
        user_object.locked = False
    user_object.incorrect_logins = 0

    session.commit()


def lock_user(session, user_or_username):
    user_object = get_user(session, user_or_username)
    user_object.locked = True
    logout_all(session, user_object.id)
    session.commit()


def open_user(session, user_or_username):
    user_object = get_user(session, user_or_username)
    user_object.locked = False
    session.commit()


def modify_user(session, user_or_username, **kwargs):
    user_object = get_user(session, user_or_username)
    for k, v in kwargs.items():
        setattr(user_object, k, v)
    session.commit()
