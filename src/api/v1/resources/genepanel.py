import copy
from api.config import config
from api.util import GenepanelConfigResolver
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
        genepanels = self.list_query(session, gene.Genepanel, schema=schemas.GenepanelSchema(), rest_filter=rest_filter)
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
        genepanel = next(gp for gp in user.group.genepanels if gp.name == name and gp.version == version)
        k = schemas.GenepanelFullSchema(strict=True).dump(genepanel).data
        return k


class GenepanelConfigResource(LogRequestResource):
    def get(self, session, name=None, version=None, gene_symbol=None):

        def find_panel(name, version):
            return session.query(gene.Genepanel) \
                    .filter(gene.Genepanel.name == name) \
                    .filter(gene.Genepanel.version == version).one_or_none()

        global_config = config['variant_criteria']['genepanel_config']

        if name is None or version is None:
            return global_config
        elif gene_symbol is None:
            genepanel = find_panel(name, version)
            if not genepanel:
                return "No genepanel found"

            gp_config_resolver = GenepanelConfigResolver(
                genepanel=genepanel
            )

            merged = gp_config_resolver.config_merged()
            return merged
        elif gene_symbol:
            genepanel = find_panel(name, version)
            if not genepanel:
                return "No genepanel found"

            gp_config_resolver = GenepanelConfigResolver(
                genepanel=genepanel
            )
            merged = gp_config_resolver.config_merged()
            override_genes = gp_config_resolver.get_genes_with_overrides()
            if gene_symbol in override_genes:
                symbol_genepanel_config = gp_config_resolver.resolve(gene_symbol)
                result = copy.deepcopy(merged)
                result.update(symbol_genepanel_config)
                return result
            else:
                return copy.deepcopy(merged)
            # return "config applicable for {}".format(gene_symbol)

        # k = schemas.GenepanelFullSchema(strict=True).dump(genepanel).data
        # return k
