import bcrypt
import datetime
import uuid
from vardb.datamodel import user

from api import schemas, ApiError
from api.util.util import paginate, rest_filter, request_json
from api.config import config

from api.v1.resource import Resource
from flask import Response, make_response


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

def _check_credentials(user, password):
    if not password_correct(user, password):
        #return Response("Invalid credentials", 401, {'WWWAuthenticate': 'Basic realm="Login Required"'})
        return False, "Invalid credentials"
    elif password_expired(user):
        return False, "Password expired"
        #return Response("Password expired", 401, {'WWWAuthenticate': 'Basic realm="Login Required"'})
    return True, "Credentials correct"

class LoginResource(Resource):
    @request_json(["username", "password"], only_required=True)
    def post(self, session, data=None):
        username = data.get("username")
        password = data.get("password")

        u = session.query(user.User).filter(user.User.username == username).one()

        credentials_correct, message = _check_credentials(u, password)
        if not credentials_correct:
            return Response(message, 401, {'WWWAuthenticate': 'Basic realm="Login Required"'})
        else:
            token = _createSession(session, u.id).token
            resp = make_response("Login successful")
            resp.set_cookie("AuthenticationToken", token, httponly=True, expires=u.password_expiry)
            return resp

class ChangePasswordResource(Resource):
    @request_json(["username", "password", "new_password"], only_required=True)
    def post(self, session, data=None):
        username = data.get("username")
        password = data.get("password")
        new_password = data.get("new_password")

        print "Login: "
        print "\tUsername: ", username
        print "\tPassword: ", password

        u = session.query(user.User).filter(user.User.username == username).one()

        credentials_correct, message = _check_credentials(u, password)
        if not credentials_correct:
            return Response(message, 401, {'WWWAuthenticate': 'Basic realm="Login Required"'})
        else:
            # Generate salt
            new_salt = bcrypt.gensalt()

            # bcrypt
            new_pwhash = bcrypt.hashpw(str(new_password), str(new_salt))

            # Set expiry date
            expiry_date = datetime.datetime.now() + datetime.timedelta(days=config["users"]["password_expiry_days"])



            # Patch user
            # print "\tOld password hash: ", pwhash
            # print "\tNew password hash: ", new_pwhash
            # print "\tOld salt: ", salt
            # print "\tNew salt: ", new_salt

            u.password = new_pwhash
            u.password_expiry = expiry_date

            # Logout existing sessions
            existing_sessions = session.query(user.UserSession).filter(
                user.UserSession.user_id == user_id
            ).all()
            for exisingUserSession in existing_sessions:
                logout(exisingUserSession)

            session.commit()
            return Response("Password for user %s changed. You can now log in." %username)
            #return schemas.UserSchema(strict=True).dump(u).data, 200




class LogoutResource(Resource):
    def patch(self, session, token):
        userSession = session.query(user.UserSession).filter(
            user.UserSession.token==token
        ).one_or_none()

        if userSession is None:
            log.warning("Trying to logout with non-existing token %s" %token)
            return

        if not userSession.valid:
            log.warning("Trying to logout with invalid token %s" %token)
            return

        logout(userSession)
        session.commit()

