from flask import request
from sqlalchemy import or_
from vardb.datamodel import sample, genotype, assessment, allele, user, gene

from api import schemas, ApiError
from api.util.util import paginate, rest_filter, rest_filter_allele

from api.util.alleledataloader import AlleleDataLoader

from api.v1.resource import Resource


class AlleleListResource(Resource):

    @rest_filter_allele
    def get(self, session, rest_filter=None,  x_filter=None, allele_ids=None):
        """
        Loads alleles based on q={} filter or allele ids directly and a={} for related entities.
        See decorator rest_filter_allele  and AlleleDataLoader for details about the possible values of a/x_filter
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
          - name: allele_ids
            in: query
            type: string
            description: List of comma separated allele ids to include
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
          - name: a
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

        if allele_ids and not rest_filter: # overwrite the q parameter with Allele id's from route variables
            rest_filter = {'id': allele_ids}

        alleles = self.list_query(session, allele.Allele, rest_filter=rest_filter)
        allele_ids = [a.id for a in alleles]
        # Optional extras
        sample_id = request.args.get('sample_id')
        gp_name = request.args.get('gp_name')
        gp_version = request.args.get('gp_version')
        annotation = request.args.get('annotation', 'true') == 'true'

        genotypes = None
        allele_genotypes = None

        if sample_id:
            genotypes = session.query(genotype.Genotype).join(sample.Sample).filter(
                sample.Sample.id == sample_id,
                or_(
                    genotype.Genotype.allele_id.in_(allele_ids),
                    genotype.Genotype.secondallele_id.in_(allele_ids),
                )
            ).all()

            # Map one genotype to each allele for use in AlleleDataLoader
            allele_genotypes = list()
            for al in alleles:
                gt = next((g for g in genotypes if g.allele_id == al.id or g.secondallele_id == al.id), None)
                if gt is None:
                    raise ApiError("No genotype match in sample {} for allele id {}".format(sample_id, al.id))
                allele_genotypes.append(gt)

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
        if x_filter:
            kwargs['x_filter'] = x_filter
        if allele_genotypes:
            kwargs['genotypes'] = allele_genotypes
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

    def get(self, session, allele_id):
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
