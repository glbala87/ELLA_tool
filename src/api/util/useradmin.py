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
def password_expired(userObj):
    return userObj.password_expiry < datetime.datetime.now()


def check_password_strength(password):
    if len(password) < config["users"]["password_minimum_length"]:
        return False

    N = config["users"]["password_num_match_groups"]
    n = sum([re.match(p, password) is not None for p in config["users"]["password_match_groups"]])
    return n >= N


def check_password(password, password_hash):
    return bcrypt.checkpw(password.encode('utf-8'), password_hash.encode('utf-8'))


def authenticate_user(session, user_or_username, password, verify_not_expired=False):
    userObj = get_user(session, user_or_username)
    if userObj.incorrect_logins >= 6:
        raise AuthenticationError("Invalid credentials. Too many failed logins. User {} is locked. Contact support to unlock.".format(userObj.username))

    if not check_password(password, userObj.password):
        userObj.incorrect_logins += 1
        session.commit()
        if userObj.incorrect_logins >= 6:
            lock_user(session, userObj)
            raise AuthenticationError("Invalid credentials. Too many failed logins. User {} has been locked. Contact support to unlock.".format(userObj.username))

        raise AuthenticationError("Invalid credentials")
    elif password_expired(userObj) and verify_not_expired:
        raise AuthenticationError("Password expired", 403)

    userObj.incorrect_logins = 0
    session.commit()
    return userObj

def hash_password(password):
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt())


# Utility functions

def create_session(session, user_id):
    token = str(uuid.uuid1())

    userSession = user.UserSession(
        token=token,
        user_id=user_id,
        issued=datetime.datetime.now(),
    )
    session.add(userSession)
    session.commit()
    return userSession


def logout(userSession):
    userSession.expired = datetime.datetime.now()

def logout_all(session, user_id):
    open_user_sessions = session.query(user.UserSession).filter(
        user.UserSession.user_id == user_id,
        user.UserSession.expired is None,
    ).all()
    for user_session in open_user_sessions:
        logout(user_session)


def change_password(session, user_or_username, old_password, new_password, override=False):
    userObj = get_user(session, user_or_username)

    if not override and not check_password(old_password, userObj.password):
        raise AuthenticationError("Invalid credentials.")

    if userObj.locked and not override:
        raise AuthenticationError("User is locked. Unable to change password. Contact support.")

    if not check_password_strength(new_password):
        raise AuthenticationError("Password doesn't follow password strength guidelines.", 403)

    old_passwords = session.query(user.OldPassword).filter(
        user.OldPassword.user_id == userObj.id
    ).order_by(
        desc(user.OldPassword.expired)
    ).limit(
        13
    ).all()


    if check_password(new_password, userObj.password):
        raise AuthenticationError("Password is equal to an old password. Choose a different password.")
    for old_pw in old_passwords:
        if check_password(new_password, old_pw.password):
            raise AuthenticationError("Password is equal to an old password. Choose a different password.")

    session.add(user.OldPassword(
        user_id=userObj.id,
        password=userObj.password
    ))
    logout_all(session, userObj.id)
    userObj.password = hash_password(new_password)
    if override:
        userObj.password_expiry = datetime.datetime.fromtimestamp(0)
    else:
        userObj.password_expiry = datetime.datetime.now()+datetime.timedelta(days=config["users"]["password_expiry_days"])

    if override:
        userObj.locked = False
    userObj.incorrect_logins = 0

    session.commit()


def lock_user(session, user_or_username):
    userObj = get_user(session, user_or_username)
    userObj.locked = True
    logout_all(session, userObj.id)
    session.commit()


def open_user(session, user_or_username):
    userObj = get_user(session, user_or_username)
    userObj.locked = False
    session.commit()


def modify_user(session, user_or_username, **kwargs):
    userObj = get_user(session, user_or_username)
    for k, v in kwargs.items():
        setattr(userObj, k, v)
    session.commit()
