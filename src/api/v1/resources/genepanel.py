from flask import request
from vardb.datamodel import gene

from api.util.util import paginate, rest_filter, authenticate
from api import schemas, ApiError
from api.v1.resource import LogRequestResource

class GenepanelListResource(LogRequestResource):

    @authenticate()
    @paginate
    @rest_filter
    def get(self, session, rest_filter=None, page=None, num_per_page=None, user=None):
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
        if rest_filter is None:
            rest_filter = dict()
        rest_filter[("name", "version")] = [(gp.name, gp.version) for gp in user.group.genepanels]
        genepanels = self.list_query(session, gene.Genepanel, schema=schemas.GenepanelFullSchema(), rest_filter=rest_filter)
        return genepanels


class GenepanelResource(LogRequestResource):

    @authenticate()
    def get(self, session, name=None, version=None, user=None):
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
          - name: include_extras
            in: query
            type: boolean
            description: Include transcripts and phenotype data
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

        genepanel = session.query(gene.Genepanel).filter(
            gene.Genepanel.name == name,
            gene.Genepanel.version == version
        ).one()
        # TODO: Restrict based on user group?

        if request.args.get('include_extras') in ['true', '1']:
            k = schemas.GenepanelFullSchema(strict=True).dump(genepanel).data
        else:
            k = schemas.GenepanelSchema(strict=True).dump(genepanel).data
        return k
