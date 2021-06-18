import copy
from flask import request
from api.config import config
from api.schemas.annotations import AnnotationConfigSchema
from api.v1.resource import LogRequestResource
from api.util.util import authenticate
from vardb.datamodel import annotation


class ConfigResource(LogRequestResource):
    @authenticate(user_config=True, optional=True)
    def get(self, session, user=None, user_config=None):
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
    def get(self, session, user=None):
        annotation_config_ids = request.args.get("annotation_config_ids").split(",")
        annotation_configs = (
            session.query(annotation.AnnotationConfig)
            .filter(annotation.AnnotationConfig.id.in_(annotation_config_ids))
            .all()
        )
        assert len(annotation_config_ids) == len(annotation_configs)
        return [AnnotationConfigSchema().dump(x).data for x in annotation_configs]
