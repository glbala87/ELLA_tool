import bcrypt
import datetime
import uuid
from vardb.datamodel import user

from api import schemas, ApiError
from api.util.util import paginate, rest_filter
from api.config import config

from api.v1.resource import Resource
from flask import Response


class UserListResource(Resource):

    @paginate
    @rest_filter
    def get(self, session, rest_filter=None, page=None, num_per_page=None):
        """
        Returns a list of users.

        * Supports `q=` filtering.
        * Supports pagination.
        ---
        summary: List users
        tags:
          - User
        parameters:
          - name: q
            in: query
            type: string
            description: JSON filter query
        responses:
          200:
            schema:
              type: array
              items:
                $ref: '#/definitions/User'
            description: List of users
        """
        return self.list_query(
            session,
            user.User,
            schemas.UserSchema(strict=True),
            rest_filter=rest_filter,
            page=page,
            num_per_page=num_per_page
        )


class UserResource(Resource):

    def get(self, session, user_id=None):
        """
        Returns a single user.
        ---
        summary: Get user
        tags:
          - User
        parameters:
          - name: user_id
            in: path
            type: integer
            description: User id
        responses:
          200:
            schema:
                $ref: '#/definitions/User'
            description: User object
        """
        if user_id is None:
            raise ApiError("No user id provided")
        u = session.query(user.User).filter(user.User.id == user_id).one()
        return schemas.UserSchema(strict=True).dump(u).data


def password_correct(user, password):
    return bcrypt.checkpw(str(password), str(user.password))

def password_expired(user):
    return user.password_expiry < datetime.datetime.now()

def check_password_strength(password):
    return True


def _createSession(session, user_id):

    # Logout existing sessions
    existing_sessions = session.query(user.Session).filter(
        user.Session.user_id == user_id
    ).all()
    for exisingUserSession in existing_sessions:
        logout(exisingUserSession)

    token = str(uuid.uuid1())

    userSession = user.Session(
        token=token,
        user_id=user_id,
        issuedate=datetime.datetime.now(),
        valid=True,
    )
    session.add(userSession)
    session.commit()
    return userSession

def logout(userSession):
    userSession.logoutdate = datetime.datetime.now()
    userSession.valid = False


class LoginResource(Resource):
    def get(self, session, username=None, password=None, new_password=None):
        print "Login: "
        print "\tUsername: ", username
        print "\tPassword: ", password

        u = session.query(user.User).filter(user.User.username == username).one()

        if not password_correct(u, password):
            return Response("Invalid credentials",401,  {'WWWAuthenticate':'Basic realm="Login Required"'})
        elif password_expired(u):
            return Response("Password expired",401,  {'WWWAuthenticate':'Basic realm="Login Required"'})
        else:
            return _createSession(session, u.id).token

    def patch(self, session, username=None, password=None, new_password=None):
        print "Login: "
        print "\tUsername: ", username
        print "\tPassword: ", password
        print "\tNew password: ", new_password

        u = session.query(user.User).filter(user.User.username == username).one()
        if not password_correct(u, password):
            return Response("Invalid credentials",401,  {'WWWAuthenticate':'Basic realm="Login Required"'})
        elif not check_password_strength(new_password):
            return Response("Password not strong enough", 403, {'WWWAuthenticate': 'Basic realm="Login Required"'})
        else:
            # Generate salt
            new_salt = bcrypt.gensalt()

            # bcrypt
            new_pwhash = bcrypt.hashpw(str(new_password), str(salt))

            # Set expiry date
            expiry_date = datetime.datetime.now() + datetime.timedelta(days=config["users"]["password_expiry_days"])

            # Patch user
            print "\tOld password hash: ", pwhash
            print "\tNew password hash: ", new_pwhash
            print "\tOld salt: ", salt
            print "\tNew salt: ", new_salt

            u.password = new_pwhash
            u.password_salt = salt
            u.password_expiry = expiry_date
            session.commit()
            return schemas.UserSchema(strict=True).dump(u).data, 200

class LogoutResource(Resource):
    def patch(self, session, token):
        userSession = session.query(user.Session).filter(
            user.Session.token==token
        ).one_or_none()

        if userSession is None:
            log.warning("Trying to logout with non-existing token %s" %token)
            return

        if not userSession.valid:
            log.warning("Trying to logout with invalid token %s" %token)
            return

        logout(userSession)
        session.commit()

