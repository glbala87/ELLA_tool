from api import config
from api.v1.resource import Resource


class ConfigResource(Resource):

    def get(self, session):
        return config.config
