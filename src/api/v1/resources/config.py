from api import config
from api.v1.resource import LogRequestResource
from api.util.util import authenticate
from vardb.datamodel import user

import collections

# https://gist.github.com/angstwad/bf22d1822c38a92ec0a9
def dict_merge(destination, src):
    """ Recursive dict merge. Inspired by :meth:``dict.update()``, instead of
    updating only top-level keys, dict_merge recurses down into dicts nested
    to an arbitrary depth, updating keys. The ``merge_dct`` is merged into
    ``dct``.
    :param destination: dict onto which the merge is executed
    :param src: dct merged into dct
    :return: None
    """
    if not src:
        return
    for k, v in src.iteritems():
        if (k in destination and isinstance(destination[k], dict)
                and isinstance(src[k], collections.Mapping)):
            dict_merge(destination[k], src[k])
        else:
            destination[k] = src[k]

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
