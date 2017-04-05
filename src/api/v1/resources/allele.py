from flask import request
from sqlalchemy import or_
from vardb.datamodel import sample, genotype, allele, gene

from api import schemas, ApiError
from api.util.util import rest_filter, link_filter, authenticate

from api.util.alleledataloader import AlleleDataLoader

from api.v1.resource import Resource


class AlleleListResource(Resource):

    @authenticate()
    @link_filter
    @rest_filter
    def get(self, session, rest_filter=None,  link_filter=None, user=None):
        """
        Loads alleles based on q={..} and link={..} for entities linked/related to those alleles.
        See decorator link_filter  and AlleleDataLoader for details about the possible values of link_filter
        Specify a genepanel to get more data included.
        Additional request parameters:
            - sample_id: Includes genotypes into the result and enables quality data in the annotation
            - annotation: Enables the annotation to filter transcripts to only show the relevant ones.
            - gp_name:
            - gp_version:

        ---
        summary: List alleles
        tags:
          - Allele
        parameters:
          - name: q
            in: query
            type: string
            description: JSON filter query
          - name: gp_name
            in: query
            type: string
            description: Genepanel name. Enables the annotation to filter transcripts to only show the relevant ones.
          - name: gp_version
            in: query
            type: string
            description: Genepanel version. Required if gp_name is provided.
          - name: annotation
            in: query
            type: boolean
            description: Whether to include annotation data or not.
          - name: link
            in: query
            type: string
            description: JSON with ids of related entities to load with the alleles
        responses:
          200:
            schema:
              type: array
              items:
                $ref: '#/definitions/Allele'
            description: List of alleles
        """

        alleles = self.list_query(session, allele.Allele, rest_filter=rest_filter)

        # Optional extras
        sample_id = request.args.get('sample_id')
        gp_name = request.args.get('gp_name')
        gp_version = request.args.get('gp_version')
        annotation = request.args.get('annotation', 'true') == 'true'

        genepanel = None
        if gp_name and gp_version:
            genepanel = session.query(gene.Genepanel).filter(
                gene.Genepanel.name == gp_name,
                gene.Genepanel.version == gp_version,
            ).one()

        kwargs = {
            'include_annotation': False,
            'include_custom_annotation': False
        }
        if link_filter:
            kwargs['link_filter'] = link_filter
        if sample_id is not None:
            kwargs['include_genotype_samples'] = [sample_id]
        if genepanel:  # TODO: make genepanel required?
            kwargs['genepanel'] = genepanel
        if annotation:
            kwargs['include_annotation'] = True
            kwargs['include_custom_annotation'] = True
        return AlleleDataLoader(session).from_objs(
            alleles,
            **kwargs
        )


class AlleleGenepanelListResource(Resource):

    @authenticate()
    def get(self, session, allele_id, user=None):
        """
        Returns a list of genepanels associated with provided allele_id.
        ---
        summary: List genepanels for one allele
        tags:
          - Allele
        parameters:
          - name: allele_id
            in: path
            type: string
            description: Allele id
        responses:
          200:
            schema:
              type: array
              items:
                $ref: '#/definitions/Genepanel'
            description: List of genepanels
        """
        genepanels = session.query(gene.Genepanel).join(
            genotype.Genotype.alleles,
            sample.Sample,
            sample.Analysis,
            gene.Genepanel
        ).filter(
            allele.Allele.id == allele_id
        ).all()

        return schemas.GenepanelSchema(strict=True).dump(genepanels, many=True).data
