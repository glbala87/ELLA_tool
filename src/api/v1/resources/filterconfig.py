from api import schemas
from api.schemas.pydantic.v1.resources import FilterConfigResponse
from api.v1.resource import LogRequestResource
from api.schemas.pydantic.v1 import validate_output
from api.util.util import authenticate
from sqlalchemy.orm import Session
from vardb.datamodel.sample import FilterConfig, UserGroupFilterConfig
from vardb.datamodel.user import User


class FilterconfigResource(LogRequestResource):
    @authenticate()
    @validate_output(FilterConfigResponse)
    def get(self, session: Session, filterconfig_id: int, **kwargs):
        filterconfig: FilterConfig = (
            session.query(FilterConfig)
            .join(UserGroupFilterConfig)
            .filter(
                FilterConfig.id == filterconfig_id,
                User.group_id == UserGroupFilterConfig.usergroup_id,
            )
            .one()
        )
        return schemas.FilterConfigSchema().dump(filterconfig).data
