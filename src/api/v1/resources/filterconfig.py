from api import schemas
from api.v1.resource import LogRequestResource
from api.util.util import authenticate
from vardb.datamodel.sample import FilterConfig, UserGroupFilterConfig
from vardb.datamodel.user import User


class FilterconfigResource(LogRequestResource):
    @authenticate()
    def get(self, session, filterconfig_id=None, user=None):
        filterconfig = (
            session.query(FilterConfig)
            .join(UserGroupFilterConfig)
            .filter(
                FilterConfig.id == filterconfig_id,
                User.group_id == UserGroupFilterConfig.usergroup_id,
            )
            .one()
        )
        return schemas.FilterConfigSchema().dump(filterconfig).data
