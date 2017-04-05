from api import config
from api.v1.resource import Resource
from api.util.util import authenticate


class ConfigResource(Resource):
    @authenticate()
    def get(self, session, user=None):
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
