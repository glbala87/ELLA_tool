from vardb.datamodel import user

from api import schemas, ApiError
from api.util.util import paginate, rest_filter, request_json, authenticate
from api.util.useradmin import authenticate_user, create_session, change_password, logout

from api.v1.resource import Resource, LogRequestResource
from flask import Response, make_response, redirect


class UserListResource(LogRequestResource):

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


class UserResource(LogRequestResource):

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


class LoginResource(Resource):
    @request_json(["username", "password"], only_required=True)
    def post(self, session, data=None):
        username = data.get("username")
        password = data.get("password")

        u = authenticate_user(session, username, password)

        token = create_session(session, u.id).token
        resp = make_response(redirect("/"))
        resp.set_cookie("AuthenticationToken", token, httponly=True, expires=u.password_expiry)

        return resp


class ChangePasswordResource(Resource):
    @request_json(["username", "password", "new_password"], only_required=True)
    def post(self, session, data=None):
        username = data.get("username")
        password = data.get("password")
        new_password = data.get("new_password")

        # change_password performs the authentication
        change_password(session, username, password, new_password)
        return Response("Password for user %s changed. You can now log in." % username)


class CurrentUser(LogRequestResource):
    @authenticate()
    def get(self, session, user=None):
        return schemas.UserSchema().dump(user).data


class LogoutResource(LogRequestResource):
    def patch(self, session, token):
        userSession = session.query(user.UserSession).filter(
            user.UserSession.token == token
        ).one_or_none()

        if userSession is None:
            log.warning("Trying to logout with non-existing token %s" % token)
            return

        if not userSession.valid:
            log.warning("Trying to logout with invalid token %s" % token)
            return

        logout(userSession)
        session.commit()

