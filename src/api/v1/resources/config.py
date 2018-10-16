import copy
from api import config
from api.v1.resource import LogRequestResource
from api.util.util import authenticate, dict_merge


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

        c = copy.deepcopy(config.config)
        if user_config:
            c["user"]["user_config"] = user_config

        return c
