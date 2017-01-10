import itertools
from collections import defaultdict
from sqlalchemy import or_, and_, func
from sqlalchemy.orm import contains_eager
from vardb.datamodel import sample, workflow, assessment, allele, genotype, gene

from api import schemas, ApiError
from api.util.util import request_json
from api.v1.resource import Resource
from api.v1 import queries

from api.util.alleledataloader import AlleleDataLoader
from api.util.interpretationdataloader import InterpretationDataLoader

from api.config import config


def load_genepanel_alleles(session, gp_allele_ids, filter_alleles=False):
    """
    Loads in allele data from AlleleDataLoader for all allele ids given by input structure:

    gp_allele_ids = {
        ('HBOC', 'v01'): [1, 2, 3, ...],
        ('HBOCutv', 'v01'): [1, 2, 3, ...],
    }

    Returns [
        {
            'genepanel': {...genepanel data...},
            'allele': {...allele data...},
            'oldest_analysis': '<dateisoformat>',
            'interpretations': [{...interpretation_data...}, ...]
        },
        ...
    ]
    """

    # Preload all alleles in one go
    all_allele_ids = list(itertools.chain(*gp_allele_ids.values()))
    all_alleles = session.query(allele.Allele).filter(allele.Allele.id.in_(all_allele_ids)).all()

    # Preload oldest analysis for each allele, to get the oldest datetime
    # for the analysis awaiting this allele's classification
    allele_ids_deposit_date = session.query(allele.Allele.id, func.min(sample.Analysis.deposit_date)).join(
        genotype.Genotype.alleles,
        sample.Sample,
        sample.Analysis
    ).filter(
        allele.Allele.id.in_(all_allele_ids)
    ).group_by(allele.Allele.id).all()

    # Preload interpretations for each allele
    allele_ids_interpretations = session.query(workflow.AlleleInterpretation).filter(
        workflow.AlleleInterpretation.allele_id.in_(all_allele_ids)
    ).all()
    allele_ids_deposit_date = {k: v for k, v in allele_ids_deposit_date}

    # Set structures/loaders
    final_alleles = list()
    genepanel_cache = dict()  # Cache for the genepanels. Ideally we'd like to just prefetch them all in single query, but turned out to be hard
    idl = InterpretationDataLoader(session, config)
    adl = AlleleDataLoader(session)
    alleleinterpretation_schema = schemas.AlleleInterpretationSchema()

    # Start processing alleles
    for gp_key, gp_allele_ids in gp_allele_ids.iteritems():  # ('HBOC', 'v01'), [1, 2, 3, ...]
        if gp_key not in genepanel_cache:
            genepanel_cache[gp_key] = session.query(gene.Genepanel).filter(
                gene.Genepanel.name == gp_key[0],
                gene.Genepanel.version == gp_key[1]
            ).one()

        genepanel = genepanel_cache[gp_key]
        genepanel_alleles = [a for a in all_alleles if a.id in gp_allele_ids]

        loaded_genepanel_alleles = adl.from_objs(
            genepanel_alleles,
            genepanel=genepanel,
            include_custom_annotation=False,  # Extra data not needed for our use cases here
            include_reference_assessments=False,
            include_allele_report=False
        )

        for a in loaded_genepanel_alleles:

            if filter_alleles and any([idl._exclude_class1(a), idl._exclude_gene(a), idl._exclude_intronic(a)]):
                continue
            else:
                interpretations = [i for i in allele_ids_interpretations if i.allele_id == a['id']]
                final_alleles.append({
                    'genepanel': {'name': genepanel.name, 'version': genepanel.version},
                    'allele': a,
                    'oldest_analysis': allele_ids_deposit_date[a['id']].isoformat(),
                    'interpretations': alleleinterpretation_schema.dump(interpretations, many=True).data
                })

    return final_alleles


class OverviewAlleleResource(Resource):

    def get_alleles_no_alleleassessment(self, session):
        """
        Returns a list of (allele + genepanel) that are missing alleleassessments.

        We only return alleles that:
            - Are missing valid alleleassessments (i.e not outdated if applicable)
            - Are connected to analyses that haven't been finalized.
            - Would not be part of the excluded_alleles for an analysisinterpretation,
              i.e that they are not frequency, intronic or gene filtered.

        Returns [{'genepanel': {'name': ..., 'version': ...}, 'allele': {...alleledata...}}, ...]
        """

        allele_ids_with_valid_aa = queries.allele_ids_with_valid_alleleassessments(session)
        allele_ids_non_finalized_analyses = queries.allele_ids_nonfinalized_analyses(session)

        candidate_allele_ids = session.query(allele.Allele.id).filter(
            allele.Allele.id.in_(allele_ids_non_finalized_analyses),
            ~allele.Allele.id.in_(allele_ids_with_valid_aa)
        ).all()

        candidate_allele_ids = [a[0] for a in candidate_allele_ids]

        # Get a list of candidate genepanels per allele id
        allele_ids_genepanels = session.query(
            workflow.AnalysisInterpretation.genepanel_name,
            workflow.AnalysisInterpretation.genepanel_version,
            allele.Allele.id
        ).join(
            genotype.Genotype.alleles,
            sample.Sample,
            sample.Analysis
        ).filter(
            workflow.AnalysisInterpretation.analysis_id == sample.Analysis.id,
            allele.Allele.id.in_(candidate_allele_ids)
        ).all()

        # Make a dict of (gp_name, gp_version): [allele_ids], since we must process as many alleles as possible at once with AlleleDataLoader
        gp_allele_ids = defaultdict(list)
        for entry in allele_ids_genepanels:
            gp_allele_ids[(entry[0], entry[1])].append(entry[2])

        # Load and return loaded allele data
        return load_genepanel_alleles(session, gp_allele_ids, filter_alleles=True)

    def get_alleles_missing_interpretation(self, session):
        alleles_no_alleleassessment = self.get_alleles_no_alleleassessment(session)

        # Only include alleles that don't already have an AlleleInterpretation
        allele_ids = [a['allele']['id'] for a in alleles_no_alleleassessment]
        allele_ids_has_interpretations = session.query(workflow.AlleleInterpretation.allele_id).filter(
            workflow.AlleleInterpretation.allele_id.in_(allele_ids)
        ).all()
        allele_ids_has_interpretations = [a[0] for a in allele_ids_has_interpretations]
        return [a for a in alleles_no_alleleassessment if a['allele']['id'] not in allele_ids_has_interpretations]

    def _get_genepanel_alleles_existing_alleleinterpretation(self, session, allele_filter):
        """
        Loads in allele data for given allele filter. Related genepanel
        for each allele is fetched from connected AlleleInterpretation.

        See load_genepanel_alleles() for more info.
        """

        # Load allele + genepanel using the connected AlleleInterpretation
        allele_ids = session.query(allele.Allele.id).filter(
            allele_filter
        ).all()

        allele_ids_genepanels = session.query(
            workflow.AlleleInterpretation.genepanel_name,
            workflow.AlleleInterpretation.genepanel_version,
            workflow.AlleleInterpretation.allele_id
        ).filter(
            workflow.AlleleInterpretation.allele_id.in_(allele_ids)
        ).all()

        # Make a dict of (gp_name, gp_version): [allele_ids],
        # for use in allele loading function
        gp_allele_ids = defaultdict(list)
        for entry in allele_ids_genepanels:
            gp_allele_ids[(entry[0], entry[1])].append(entry[2])

        return load_genepanel_alleles(session, gp_allele_ids)

    def get_alleles_ongoing(self, session):
        return self._get_genepanel_alleles_existing_alleleinterpretation(
            session,
            allele.Allele.id.in_(queries.workflow_alleles_ongoing(session))
        )

    def get_alleles_markedreview(self, session):
        return self._get_genepanel_alleles_existing_alleleinterpretation(
            session,
            allele.Allele.id.in_(queries.workflow_alleles_marked_review(session))
        )

    def get_alleles_finalized(self, session):
        return self._get_genepanel_alleles_existing_alleleinterpretation(
            session,
            allele.Allele.id.in_(queries.workflow_alleles_finalized(session))
        )

    def get(self, session):
        return {
            'missing_alleleassessment': self.get_alleles_missing_interpretation(session),
            'marked_review': self.get_alleles_markedreview(session),
            'ongoing': self.get_alleles_ongoing(session),
            'finalized': self.get_alleles_finalized(session)
        }


class OverviewAnalysisResource(Resource):

    def get_categorized_analyses(self, session):

        # Get all (analysis_id, allele_id) combinations for analyses that are 'Not started'.
        # We want to categorize these analyses into with_findings, without_findings and missing_alleleassessments
        # based on the state of their alleles' alleleassessments

        # First get rid of all variants that would be filtered out, per analysis
        workflow_analyses_not_started = queries.workflow_analyses_not_started(session)
        analysis_ids_allele_ids = session.query(sample.Analysis.id, allele.Allele.id).join(
            genotype.Genotype.alleles,
            sample.Sample,
            sample.Analysis,
        ).filter(
            sample.Analysis.id.in_(workflow_analyses_not_started)
        ).all()

        # Now we have all the alleles, so what remains is to see which alleles are
        # filtered out, which have findings, which are normal and which are without alleleassessments
        # For performance, we first categorize allele ids, then connect them to the analyses afterwards
        all_allele_ids = [a[1] for a in analysis_ids_allele_ids]

        # Get a list of candidate genepanels per allele id
        allele_ids_genepanels = session.query(
            workflow.AnalysisInterpretation.genepanel_name,
            workflow.AnalysisInterpretation.genepanel_version,
            allele.Allele.id
        ).join(
            genotype.Genotype.alleles,
            sample.Sample,
            sample.Analysis
        ).filter(
            workflow.AnalysisInterpretation.analysis_id == sample.Analysis.id,
            allele.Allele.id.in_(all_allele_ids)
        ).all()

        # Make a dict of (gp_name, gp_version): [allele_ids], since we must process as many alleles as possible at once with AlleleDataLoader
        gp_allele_ids = defaultdict(list)
        for entry in allele_ids_genepanels:
            gp_allele_ids[(entry[0], entry[1])].append(entry[2])

        # Filter out alleles (it also loads the data, which we don't really need here)
        genepanels_alleles = load_genepanel_alleles(session, gp_allele_ids, filter_alleles=True)
        filtered_allele_ids = list(set([a['allele']['id'] for a in genepanels_alleles]))

        classification_options = config['classification']['options']
        classification_findings = [o['value'] for o in classification_options if o.get('include_analysis_with_findings')]
        classification_wo_findings = [o['value'] for o in classification_options if not o.get('include_analysis_with_findings')]

        categorized_allele_ids = {

            'with_findings': session.query(assessment.AlleleAssessment.allele_id).filter(
                assessment.AlleleAssessment.allele_id.in_(filtered_allele_ids),
                assessment.AlleleAssessment.classification.in_(classification_findings),
                *queries.valid_alleleassessments_filter(session)
            ).all(),

            'without_findings': session.query(assessment.AlleleAssessment.allele_id).filter(
                assessment.AlleleAssessment.allele_id.in_(filtered_allele_ids),
                assessment.AlleleAssessment.classification.in_(classification_wo_findings),
                *queries.valid_alleleassessments_filter(session)
            ).all(),

            'missing_alleleassessments': session.query(allele.Allele.id).outerjoin(assessment.AlleleAssessment).filter(
                allele.Allele.id.in_(filtered_allele_ids),
                assessment.AlleleAssessment.allele_id.is_(None)
            ).all()

        }

        # Strip out the tuples..
        categorized_allele_ids = {k: [a[0] for a in v] for k, v in categorized_allele_ids.iteritems()}

        # Now we can check our analyses and categorize them
        # Sort into {analysis_id: [allele_ids]}
        analysis_ids_allele_ids_map = defaultdict(list)
        for a in analysis_ids_allele_ids:
            if a[1] in filtered_allele_ids:
                analysis_ids_allele_ids_map[a[0]].append(a[1])

        analyses_not_started = session.query(sample.Analysis).filter(
            sample.Analysis.id.in_(workflow_analyses_not_started)
        ).all()
        aschema = schemas.AnalysisSchema()
        analyses_not_started_serialized = [aschema.dump(a).data for a in analyses_not_started]

        final_analyses = {
            'with_findings': [],
            'without_findings': [],
            'missing_alleleassessments': []
        }

        for analysis_id, allele_ids in analysis_ids_allele_ids_map.iteritems():
            analysis = next(a for a in analyses_not_started_serialized if a['id'] == analysis_id)
            if any(a in categorized_allele_ids['missing_alleleassessments'] for a in allele_ids):
                final_analyses['missing_alleleassessments'].append(analysis)
            elif any(a in categorized_allele_ids['with_findings'] for a in allele_ids):
                final_analyses['with_findings'].append(analysis)
            elif all(a in categorized_allele_ids['without_findings'] for a in allele_ids):
                final_analyses['without_findings'].append(analysis)
            else:
                raise ApiError("Allele was not categorized correctly. This may indicate a bug.")

        # Add the rest of categories
        other_categories = [
            ('marked_review', queries.workflow_analyses_marked_review(session)),
            ('ongoing', queries.workflow_analyses_ongoing(session)),
            ('finalized', queries.workflow_analyses_finalized(session))
        ]

        for key, subquery in other_categories:
            analyses = session.query(sample.Analysis).filter(
                sample.Analysis.id.in_(subquery)
            ).all()
            final_analyses[key] = [aschema.dump(a).data for a in analyses]

        return final_analyses

    def get(self, session):

        return self.get_categorized_analyses(session)
