import copy

from api.config import config
from api.schemas.annotations import AnnotationConfigSchema
from api.schemas.pydantic.v1 import validate_output
from api.schemas.pydantic.v1.config import UserConfig
from api.schemas.pydantic.v1.resources import AnnotationConfigListResponse, ConfigResponse
from api.util.util import authenticate
from api.v1.resource import LogRequestResource
from flask import request
from sqlalchemy.orm import Session
from vardb.datamodel import annotation


class ConfigResource(LogRequestResource):
    @authenticate(user_config=True, optional=True, pydantic=True)
    @validate_output(ConfigResponse)
    def get(self, user_config: UserConfig, **kwargs):
        """
        Returns application configuration.
        ---
        summary: Get config
        tags:
          - Config
        responses:
          200:
            schema:
                type: object
            description: Config object
        """

        c = copy.deepcopy(config)
        if user_config:
            c["user"]["user_config"] = user_config

        return c


class AnnotationConfigListResource(LogRequestResource):
    @authenticate()
    @validate_output(AnnotationConfigListResponse)
    def get(self, session: Session, **kwargs):
        raw_ids = request.args.get("annotation_config_ids")
        if raw_ids is None:
            raise ValueError("No annotation_config_ids specified")
        annotation_config_ids = [int(i) for i in raw_ids.split(",")]
        annotation_configs = (
            session.query(annotation.AnnotationConfig)
            .filter(annotation.AnnotationConfig.id.in_(annotation_config_ids))
            .all()
        )
        assert len(annotation_config_ids) == len(annotation_configs)
        return [AnnotationConfigSchema().dump(x).data for x in annotation_configs]
