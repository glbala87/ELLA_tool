from vardb.datamodel import gene

from api import schemas, ApiError
from api.v1.resource import Resource


class GenepanelResource(Resource):

    def get(self, session, name=None, version=None):
        if name is None:
            raise ApiError("No genepanel name is provided")
        if version is None:
            raise ApiError("No genepanel version is provided")
        genepanel = session.query(gene.Genepanel) \
                    .filter(gene.Genepanel.name == name) \
                    .filter(gene.Genepanel.version == version).one()
        return schemas.GenepanelSchema(strict=True).dump(genepanel).data
