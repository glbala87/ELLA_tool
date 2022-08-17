import logging
from typing import Dict, Optional

from api import ApiError, schemas
from api.schemas.pydantic.v1 import validate_output
from api.schemas.pydantic.v1.resources import (
    ChangePasswordRequest,
    EmptyResponse,
    LoginRequest,
    UserListResponse,
    UserResponse,
)
from api.util.useradmin import (
    authenticate_user,
    change_password,
    create_session,
    get_usersession_by_token,
    logout,
)
from api.util.util import authenticate, paginate, request_json, rest_filter
from api.v1.resource import LogRequestResource, Resource
from flask import make_response, request
from sqlalchemy.orm import Session, aliased
from vardb.datamodel import user as user_model

log = logging.getLogger(__name__)


class UserListResource(LogRequestResource):
    @authenticate()
    @validate_output(UserListResponse, paginated=True)
    @paginate
    @rest_filter
    def get(
        self,
        session: Session,
        rest_filter: Optional[Dict],
        page: int,
        per_page: int,
        user: user_model.User,
        **kwargs
    ):
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
    @validate_output(UserResponse)
    def get(self, session: Session, user_id: user_model.User):
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
    @request_json(model=LoginRequest)
    def post(self, session: Session, data: LoginRequest):
        u = authenticate_user(session, data.username, data.password)

        token = create_session(session, u.id)
        resp = make_response()
        resp.set_cookie("AuthenticationToken", token, httponly=True, expires=u.password_expiry)

        return resp


class ChangePasswordResource(Resource):
    @validate_output(EmptyResponse)
    @request_json(model=ChangePasswordRequest)
    def post(self, session: Session, data: ChangePasswordRequest):
        # change_password performs the authentication
        change_password(session, data.username, data.password, data.new_password)


class CurrentUser(LogRequestResource):
    @authenticate()
    @validate_output(UserResponse)
    def get(self, session: Session, user: user_model.User):
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
        # this is not getting included in schema dump above in tests for some reason?
        if not dumped_user.get("user_group_name"):
            dumped_user["user_group_name"] = dumped_user["group"]["name"]
        return dumped_user


class LogoutResource(LogRequestResource):
    @authenticate()
    @validate_output(EmptyResponse)
    def post(self, session: Session, **kwargs):
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
