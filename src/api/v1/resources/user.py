import logging
from flask import make_response, redirect, request
from sqlalchemy.orm import aliased
from vardb.datamodel import user as user_model

from api import schemas, ApiError
from api.util.util import paginate, rest_filter, request_json, authenticate
from api.util.useradmin import (
    authenticate_user,
    create_session,
    change_password,
    logout,
    get_usersession_by_token,
)

from api.v1.resource import Resource, LogRequestResource

log = logging.getLogger(__name__)


class UserListResource(LogRequestResource):
    @authenticate()
    @paginate
    @rest_filter
    def get(self, session, rest_filter=None, page=None, per_page=None, user=None):
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
        rest_filter["group_id"] = user.group_id

        return self.list_query(
            session,
            user_model.User,
            schemas.UserFullSchema(strict=True),
            rest_filter=rest_filter,
            page=page,
            per_page=per_page,
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
    @request_json(required_fields=["username", "password"], strict=True)
    def post(self, session, data=None):
        username = data.get("username")
        password = data.get("password")

        u = authenticate_user(session, username, password)

        token = create_session(session, u.id)
        resp = make_response(redirect("/"))
        resp.set_cookie("AuthenticationToken", token, httponly=True, expires=u.password_expiry)

        return resp


class ChangePasswordResource(Resource):
    @request_json(required_fields=["username", "password", "new_password"], strict=True)
    def post(self, session, data=None):
        username = data.get("username")
        password = data.get("password")
        new_password = data.get("new_password")

        # change_password performs the authentication
        change_password(session, username, password, new_password)


class CurrentUser(LogRequestResource):
    @authenticate()
    def get(self, session, user=None):
        # Load import_groups into user group
        usergroupimport = aliased(user_model.UserGroup)
        importgroups = (
            session.query(user_model.UserGroup.name, usergroupimport.name)
            .join(
                user_model.UserGroupImport,
                user_model.UserGroup.id == user_model.UserGroupImport.c.usergroup_id,
            )
            .join(
                usergroupimport,
                usergroupimport.id == user_model.UserGroupImport.c.usergroupimport_id,
            )
            .filter(user_model.UserGroup.id == user.group.id)
            .all()
        )
        dumped_user = schemas.UserFullSchema().dump(user).data
        import_group_names = [a[1] for a in importgroups]
        dumped_user["group"]["import_groups"] = import_group_names
        return dumped_user


class LogoutResource(LogRequestResource):
    @authenticate()
    def post(self, session, user=None):

        token = request.cookies.get("AuthenticationToken")  # We only logout specific token

        user_session = get_usersession_by_token(session, token)

        if user_session is None:
            log.warning("Trying to logout with non-existing token %s" % token)
            return

        if user_session.logged_out:
            log.warning("Trying to logout already logged out token %s" % token)
            return

        logout(user_session)
        session.commit()
