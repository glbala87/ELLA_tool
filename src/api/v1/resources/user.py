import logging
from vardb.datamodel import user as user_model

from api import schemas, ApiError
from api.util.util import paginate, rest_filter, request_json, authenticate
from api.util.useradmin import authenticate_user, create_session, change_password, logout

from api.v1.resource import Resource, LogRequestResource
from flask import Response, make_response, redirect, request

log = logging.getLogger(__name__)


class UserListResource(LogRequestResource):

    @authenticate()
    @paginate
    @rest_filter
    def get(self, session, rest_filter=None, page=None, num_per_page=None, user=None):
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
        if rest_filter is None:
            rest_filter = {}
        rest_filter["group_id"] = user.group_id;

        return self.list_query(
            session,
            user_model.User,
            schemas.UserFullSchema(strict=True),
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
        u = session.query(user_model.User).filter(user_model.User.id == user_id).one()
        return schemas.UserFullSchema(strict=True).dump(u).data


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
        return schemas.UserFullSchema().dump(user).data


class LogoutResource(LogRequestResource):

    @authenticate()
    def post(self, session, user=None):

        token = request.cookies.get("AuthenticationToken")  # We only logout specific token
        user_session = session.query(user_model.UserSession).filter(
            user_model.UserSession.token == token
        ).one_or_none()
        if user_session is None:
            log.warning("Trying to logout with non-existing token %s" % token)
            return

        if user_session.logged_out:
            log.warning("Trying to logout already logged out token %s" % token)
            return

        logout(user_session)
        session.commit()

