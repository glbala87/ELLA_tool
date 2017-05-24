from api import config
from api.v1.resource import LogRequestResource


class ConfigResource(LogRequestResource):
    def get(self, session):
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
        return config.config
