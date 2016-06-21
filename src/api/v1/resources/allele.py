from flask import request
from sqlalchemy import or_
from vardb.datamodel import sample, genotype, assessment, allele, user, gene

from api import schemas, ApiError
from api.util.util import paginate, rest_filter

from api.util.alleledataloader import AlleleDataLoader

from api.v1.resource import Resource


class AlleleListResource(Resource):

    @rest_filter
    def get(self, session, rest_filter=None, allele_ids=None):
        """
        Loads alleles based on q={} filter or  allele ids directly
        Additional parameters:
            - sample_id: Includes genotypes into the result and enables quality data in the annotation
            - genepanel: Enables the annotation to filter transcripts to only show the relevant ones.
            -
        """

        if allele_ids and not rest_filter:
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


class AlleleAnalysisListResource(Resource):

    def get(self, session, allele_id):
        analyses = session.query(sample.Analysis).join(
            genotype.Genotype.alleles,
            sample.Sample,
            sample.Analysis
        ).filter(
            allele.Allele.id == allele_id
        ).all()

        return schemas.AnalysisSchema(strict=True).dump(analyses, many=True).data
