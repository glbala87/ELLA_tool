from api import schemas, ApiError
from api.v1.resource import LogRequestResource
from api.util.util import authenticate
from vardb.datamodel.sample import FilterConfig
from vardb.datamodel.user import User, UserGroup


class FilterconfigResource(LogRequestResource):
    @authenticate()
    def get(self, session, filterconfig_id=None, user=None):
        filterconfig = (
            session.query(FilterConfig)
            .join(UserGroup, User)
            .filter(FilterConfig.id == filterconfig_id, User.id == user.id)
            .one()
        )
        return schemas.FilterConfigSchema().dump(filterconfig).data
