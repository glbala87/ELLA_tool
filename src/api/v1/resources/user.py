from vardb.datamodel import user

from api import schemas, ApiError
from api.util.util import paginate, rest_filter

from api.v1.resource import Resource


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
