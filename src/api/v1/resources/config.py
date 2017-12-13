from api import config
from api.v1.resource import LogRequestResource
from api.util.util import authenticate, dict_merge


class ConfigResource(LogRequestResource):
    @authenticate(optional=True)
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

        c = config.config
        if user is not None:
            dict_merge(c["user"]["user_config"], user.group.config)
            dict_merge(c["user"]["user_config"], user.config)

        return c
