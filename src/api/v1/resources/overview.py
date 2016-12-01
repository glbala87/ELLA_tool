import datetime
from collections import defaultdict
from sqlalchemy import or_, and_
from sqlalchemy.orm import contains_eager
from vardb.datamodel import sample, workflow, assessment, allele, genotype, gene

from api import schemas, ApiError
from api.util.util import request_json
from api.v1.resource import Resource

from api.util.alleledataloader import AlleleDataLoader
from api.util.interpretationdataloader import InterpretationDataLoader

from api.config import config


class OverviewAlleleInterpretationResource(Resource):

    def get_alleles_no_alleleassessment(self, session):
        """
        Returns a list of alleles that are missing alleleinterpretations.

        We only return alleles that:
            - Are missing valid alleleassessments (i.e not outdated if applicable)
            - Are connected to analyses that haven't been finalized.
            - Would not be part of the excluded_alleles for an analysisinterpretation,
              i.e that they are not frequency, intronic or gene filtered.

        """
        # Here be dragons...

        # Subquery: Alleles with alleleassessments that are still valid
        classification_filters = list()
        # Create classification filters, filtering on classification and optionally outdated threshold
        for option in config['classification']['options']:
            internal_filters = [assessment.AlleleAssessment.classification == option['value']]
            if 'outdated_after_days' in option:
                outdated_time = datetime.datetime.now() - datetime.timedelta(days=option['outdated_after_days'])
                internal_filters.append(assessment.AlleleAssessment.date_last_update > outdated_time)
            # Add our filter using and_
            classification_filters.append(and_(*internal_filters))

        allele_ids_with_valid_aa = session.query(allele.Allele.id).join(assessment.AlleleAssessment).filter(
            or_(*classification_filters),
            assessment.AlleleAssessment.date_superceeded.is_(None)
        )

        # Subquery: Alleles in non-finalized analyses
        allele_ids_non_finalized_analyses = session.query(
            allele.Allele.id,
        ).join(
            genotype.Genotype.alleles,
            sample.Sample,
            sample.Analysis,
            sample.Interpretation
        ).filter(
            or_(
                sample.Interpretation.status == 'Not started',
                sample.Interpretation.status == 'Ongoing'
            )
        )

        candidate_alleles = session.query(allele.Allele).filter(
            allele.Allele.id.in_(allele_ids_non_finalized_analyses),
            ~allele.Allele.id.in_(allele_ids_with_valid_aa)
        ).all()

        # Now to the complicated stuff...
        # TODO: Major performance problem when many alleles..ideally we want to do all filtering in SQL
        # We want to filter out the FREQUENCY, INTRONIC and GENE filtered variants.
        # For this we need to use the genepanel, and one allele can belong to several analyses,
        # so in practice we can have multiple gene panels per allele.
        # We get a list of candidate genepanels per allele id

        allele_ids_genepanels = session.query(
            gene.Genepanel.name,
            gene.Genepanel.version,
            allele.Allele.id
        ).join(
            genotype.Genotype.alleles,
            sample.Sample,
            sample.Analysis
        ).filter(
            allele.Allele.id.in_([a.id for a in candidate_alleles]),
            sample.Analysis.genepanel_name == gene.Genepanel.name,
            sample.Analysis.genepanel_version == gene.Genepanel.version,
        ).all()

        # Make a dict of (gp_name, gp_version): [allele_ids], since we must process as many alleles as possible at once with AlleleDataLoader
        gp_allele_ids = defaultdict(list)
        for entry in allele_ids_genepanels:
            gp_allele_ids[(entry[0], entry[1])].append(entry[2])

        idl = InterpretationDataLoader(session, config)
        genepanel_cache = dict()  # Cache for the genepanels. Ideally we'd like to just prefetch them all in single query, but turned out to be hard
        final_allele_ids = set()

        for gp_key, allele_ids in gp_allele_ids.iteritems():
            if gp_key not in genepanel_cache:
                genepanel_cache[gp_key] = session.query(gene.Genepanel).filter(
                    gene.Genepanel.name == gp_key[0],
                    gene.Genepanel.version == gp_key[1]
                ).one()
            genepanel = genepanel_cache[gp_key]
            genepanel_alleles = [a for a in candidate_alleles if a.id in allele_ids]
            loaded_genepanel_alleles = AlleleDataLoader(session).from_objs(  # This is the performance bottleneck...
                genepanel_alleles,
                genepanel=genepanel,
                include_custom_annotation=False,  # Extra data not needed for the filtering we're going to do
                include_reference_assessments=False,
                include_allele_report=False
            )

            final_allele_ids.update([a['id'] for a in loaded_genepanel_alleles if not any([idl._exclude_class1(a), idl._exclude_gene(a), idl._exclude_intronic(a)])])

        return sorted(final_allele_ids)

    def get(self, session):

        return {
            'alleles': {
                'missing_alleleassessment': self.get_alleles_no_alleleassessment(session)
            },
            'analysis': {
                'class3to5': [],
                'normal': []
            }
        }, 200

if __name__ == '__main__':
    from vardb.util import DB
    db = DB()
    db.connect()

    print OverviewAlleleInterpretationResource().get(db.session)