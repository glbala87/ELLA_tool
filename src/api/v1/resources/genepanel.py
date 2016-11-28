from vardb.datamodel import gene

from api.util.util import paginate, rest_filter
from api import schemas, ApiError
from api.v1.resource import Resource

class GenepanelListResource(Resource):
    @paginate
    @rest_filter
    def get(self, session, rest_filter=None, page=None, num_per_page=None):
        """
        Returns a list of genepanles.

        * Supports `q=` filtering.
        * Supports pagination.
        ---
        summary: List genepanels
        tags:
          - Genepanel
        parameters:
          - name: q
            in: query
            type: string
            description: JSON filter query
        responses:
          200:
            schema:
              type: array
              items:
                $ref: '#/definitions/Genepanel'
            description: List of genepanels
        """
        genepanels = self.list_query(session, gene.Genepanel, schema=schemas.GenepanelSchema(), rest_filter=rest_filter)
        return genepanels

class GenepanelResource(Resource):
    def get(self, session, name=None, version=None):
        """
        Returns a single genepanel.
        ---
        summary: Get genepanel
        tags:
          - Genepanel
        parameters:
          - name: name
            in: path
            type: string
            description: Genepanel name
          - name: version
            in: path
            type: string
            description: Genepanel version
        responses:
          200:
            schema:
                $ref: '#/definitions/Genepanel'
            description: Genepanel object
        """
        if name is None:
            raise ApiError("No genepanel name is provided")
        if version is None:
            raise ApiError("No genepanel version is provided")
        genepanel = session.query(gene.Genepanel) \
                    .filter(gene.Genepanel.name == name) \
                    .filter(gene.Genepanel.version == version).one()
        k = schemas.GenepanelSchema(strict=True).dump(genepanel).data
        return k
