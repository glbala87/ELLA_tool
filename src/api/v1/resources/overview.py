import itertools
import datetime
import pytz
from collections import defaultdict
from sqlalchemy import func, tuple_, or_, and_
from vardb.datamodel import sample, workflow, assessment, allele, genotype, gene, user as model_user

from api import schemas, ApiError
from api.v1.resource import LogRequestResource
from api.util import queries
from api.util.util import authenticate
from api.util.allelefilter import AlleleFilter
from api.util.alleledataloader import AlleleDataLoader

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

    # Filter out alleles
    if filter_alleles:
        af = AlleleFilter(session, config)
        gp_nonfiltered_alleles = af.filter_alleles(gp_allele_ids)
        final_gp_allele_ids = {k: v['allele_ids'] for k, v in gp_nonfiltered_alleles.iteritems()}
    else:
        final_gp_allele_ids = gp_allele_ids

    all_allele_ids = list(itertools.chain.from_iterable(final_gp_allele_ids.values()))

    # Preload all alleles
    all_alleles = session.query(allele.Allele).filter(
        allele.Allele.id.in_(all_allele_ids)
    ).all()

    # Preload oldest analysis for each allele, to get the oldest datetime
    # for the analysis awaiting this allele's classification
    allele_ids_deposit_date = session.query(allele.Allele.id, func.min(sample.Analysis.deposit_date)).join(
        genotype.Genotype.alleles,
        sample.Sample,
        sample.Analysis
    ).filter(
        allele.Allele.id.in_(all_allele_ids)
    ).group_by(allele.Allele.id).all()
    allele_ids_deposit_date = {k: v for k, v in allele_ids_deposit_date}

    # Preload highest priority analysis for each allele
    allele_ids_priority = session.query(allele.Allele.id, func.max(sample.Analysis.priority)).join(
        genotype.Genotype.alleles,
        sample.Sample,
        sample.Analysis
    ).filter(
        allele.Allele.id.in_(all_allele_ids)
    ).group_by(allele.Allele.id).all()
    allele_ids_priority = {k: v for k, v in allele_ids_priority}

    # Preload interpretations for each allele
    allele_ids_interpretations = session.query(workflow.AlleleInterpretation).filter(
        workflow.AlleleInterpretation.allele_id.in_(all_allele_ids)
    ).all()

    # Preload genepanels
    genepanels = session.query(gene.Genepanel).filter(
        tuple_(gene.Genepanel.name, gene.Genepanel.version).in_(gp_allele_ids.keys())
    ).all()

    # Set structures/loaders
    final_alleles = list()
    adl = AlleleDataLoader(session)
    alleleinterpretation_schema = schemas.AlleleInterpretationOverviewSchema()

    # Create output data
    for gp_key, allele_ids in final_gp_allele_ids.iteritems():  # ('HBOC', 'v01'), [1, 2, 3, ...]

        genepanel = next(g for g in genepanels if g.name == gp_key[0] and g.version == gp_key[1])
        gp_alleles = [a for a in all_alleles if a.id in allele_ids]

        loaded_genepanel_alleles = adl.from_objs(
            gp_alleles,
            genepanel=genepanel,
            include_allele_assessment=True,  # Needed for correct filtering
            include_custom_annotation=False,  # Rest is extra data not needed for our use cases here
            include_reference_assessments=False,
            include_allele_report=False
        )

        for a in loaded_genepanel_alleles:
            interpretations = [i for i in allele_ids_interpretations if i.allele_id == a['id']]
            final_alleles.append({
                'genepanel': {'name': genepanel.name, 'version': genepanel.version},
                'allele': a,
                'oldest_analysis': allele_ids_deposit_date.get(a['id'], datetime.datetime.now(pytz.utc)).isoformat(),
                'highest_analysis_priority': allele_ids_priority.get(a['id'], 1),  # If there's no analysis connected, set to normal priority
                'interpretations': alleleinterpretation_schema.dump(interpretations, many=True).data
            })

    return final_alleles


class OverviewAlleleResource(LogRequestResource):
    def get_alleles_no_alleleassessment(self, session, user=None):
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

    def get_alleles_missing_interpretation(self, session, user=None):
        alleles_no_alleleassessment = self.get_alleles_no_alleleassessment(session)

        # Only include alleles that don't already have an AlleleInterpretation
        allele_ids = [a['allele']['id'] for a in alleles_no_alleleassessment]
        allele_ids_has_interpretations = session.query(workflow.AlleleInterpretation.allele_id).filter(
            workflow.AlleleInterpretation.allele_id.in_(allele_ids)
        ).all()
        allele_ids_has_interpretations = [a[0] for a in allele_ids_has_interpretations]
        return [a for a in alleles_no_alleleassessment if a['allele']['id'] not in allele_ids_has_interpretations]

    def _get_genepanel_alleles_existing_alleleinterpretation(self, session, allele_filter, user=None):
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

        return load_genepanel_alleles(session, gp_allele_ids, filter_alleles=False)  # Don't filter out for existing interpretations

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

    def get_alleles_not_started(self, session):
        return self._get_genepanel_alleles_existing_alleleinterpretation(
            session,
            allele.Allele.id.in_(queries.workflow_alleles_not_started(session))
        )

    @authenticate()
    def get(self, session, user=None):
        return {
            'missing_alleleassessment': self.get_alleles_missing_interpretation(session)+self.get_alleles_not_started(session),
            'marked_review': self.get_alleles_markedreview(session),
            'ongoing': self.get_alleles_ongoing(session),
            'finalized': self.get_alleles_finalized(session)
        }


class OverviewAnalysisResource(LogRequestResource):

    def _categorize_allele_ids_findings(self, session, allele_ids):
        """
        Categorizes alleles based on their classification findings.
        A finding is defined from the 'include_analysis_with_findings' flag in config.

        The allele ids are divided into three categories:

        - with_findings:
            alleles that have valid alleleassessments and classification is in findings.

        - with_findings:
            alleles that have valid alleleassessments, but classification is not in findings.

        - missing_alleleassessments:
            alleles that are missing alleleassessments or the alleleassessment is outdated.

        :returns: A dict() of set()
        """
        classification_options = config['classification']['options']
        classification_findings = [o['value'] for o in classification_options if o.get('include_analysis_with_findings')]
        classification_wo_findings = [o['value'] for o in classification_options if not o.get('include_analysis_with_findings')]

        categorized_allele_ids = {

            'with_findings': session.query(assessment.AlleleAssessment.allele_id).filter(
                assessment.AlleleAssessment.allele_id.in_(allele_ids),
                assessment.AlleleAssessment.classification.in_(classification_findings),
                *queries.valid_alleleassessments_filter(session)
            ).all(),

            'without_findings': session.query(assessment.AlleleAssessment.allele_id).filter(
                assessment.AlleleAssessment.allele_id.in_(allele_ids),
                assessment.AlleleAssessment.classification.in_(classification_wo_findings),
                *queries.valid_alleleassessments_filter(session)
            ).all(),

            'missing_alleleassessments': session.query(allele.Allele.id).outerjoin(assessment.AlleleAssessment).filter(
                allele.Allele.id.in_(allele_ids),
                or_(
                    assessment.AlleleAssessment.allele_id.is_(None),  # outerjoin() gives null values when missing alleleassessment
                    ~and_(*queries.valid_alleleassessments_filter(session))  # Include cases where classification isn't valid anymore (notice inversion operator)
                ),
                # The filter below is part of the queries.valid_alleleassessments_filter above.
                # Since we negate that query, we end up including all alleleassessment that are superceeded.
                # We therefore need to explicitly exclude those here.
                assessment.AlleleAssessment.date_superceeded.is_(None)
            ).all()
        }

        # Strip out the tuples from db results and convert to set()
        categorized_allele_ids = {k: set([a[0] for a in v]) for k, v in categorized_allele_ids.iteritems()}
        return categorized_allele_ids

    def get_categorized_analyses(self, session):

        # Get all (analysis_id, allele_id) combinations for analyses that are 'Not started'.
        # We want to categorize these analyses into with_findings, without_findings and missing_alleleassessments
        # based on the state of their alleles' alleleassessments

        # First fetch all not-started analyses, with their allele_ids
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
        # For performance, we first categorize the allele ids in isolation,
        # then connect them to the analyses afterwards
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

        # Make a dict of (gp_name, gp_version): [allele_ids] for use with AlleleFilter
        gp_allele_ids = defaultdict(list)
        for entry in allele_ids_genepanels:
            gp_allele_ids[(entry[0], entry[1])].append(entry[2])

        # Filter out alleles
        af = AlleleFilter(session, config)
        gp_nonfiltered_allele_ids = af.filter_alleles(gp_allele_ids)
        nonfiltered_allele_ids = set(itertools.chain.from_iterable([v['allele_ids'] for v in gp_nonfiltered_allele_ids.values()]))

        # Now we can start to check our analyses and categorize them
        # First, sort into {analysis_id: [allele_ids]}
        analysis_ids_allele_ids_map = defaultdict(set)
        for a in analysis_ids_allele_ids:
            analysis_ids_allele_ids_map[a[0]].add(a[1])

        # Load analysis data to insert into final response
        analyses_not_started = session.query(sample.Analysis).filter(
            sample.Analysis.id.in_(workflow_analyses_not_started)
        ).all()
        aschema = schemas.AnalysisSchema()
        analyses_not_started_serialized = aschema.dump(analyses_not_started, many=True).data

        final_analyses = {
            'with_findings': [],
            'without_findings': [],
            'missing_alleleassessments': []
        }

        # Next, compare the allele ids for each analysis and see which category they end up in
        # with regards to the categorized_allele_ids we created earlier.
        # Working with sets only for simplicity (& is intersection, < is subset)
        categorized_allele_ids = self._categorize_allele_ids_findings(session, nonfiltered_allele_ids)
        for analysis_id, analysis_allele_ids in analysis_ids_allele_ids_map.iteritems():
            analysis_nonfiltered_allele_ids = analysis_allele_ids & nonfiltered_allele_ids
            analysis_filtered_allele_ids = analysis_allele_ids - analysis_nonfiltered_allele_ids
            analysis = next(a for a in analyses_not_started_serialized if a['id'] == analysis_id)

            # One or more allele is missing alleleassessment
            if analysis_nonfiltered_allele_ids & categorized_allele_ids['missing_alleleassessments']:
                final_analyses['missing_alleleassessments'].append(analysis)
            # One or more allele has a finding
            elif analysis_nonfiltered_allele_ids & categorized_allele_ids['with_findings']:
                final_analyses['with_findings'].append(analysis)
            # All alleles are without findings
            # Special case: All alleles were filtered out. Treat as without_findings.
            elif ((analysis_nonfiltered_allele_ids and
                   analysis_nonfiltered_allele_ids <= categorized_allele_ids['without_findings']) or
                  analysis_allele_ids == analysis_filtered_allele_ids):
                final_analyses['without_findings'].append(analysis)
            # All possible cases should have been taken care of above
            else:
                raise ApiError("Allele was not categorized correctly. This may indicate a bug.")

        # Finally, add the rest of the categories and their analysis data
        other_categories = [
            ('marked_review', queries.workflow_analyses_marked_review(session)),
            ('ongoing', queries.workflow_analyses_ongoing(session)),
            ('finalized', queries.workflow_analyses_finalized(session))
        ]

        for key, subquery in other_categories:
            analyses = session.query(sample.Analysis).filter(
                sample.Analysis.id.in_(subquery)
            ).all()
            final_analyses[key] = aschema.dump(analyses, many=True).data

        return final_analyses

    @authenticate()
    def get(self, session, user=None):

        return self.get_categorized_analyses(session)


class OverviewDashboardResource(LogRequestResource):

    @authenticate()
    def get(self, session, user=None):
        """
        Provides dashboard data for authenticated user.
        """

        # Get latest workflows where the user has been involved
        sq_wf_allele_user = session.query(workflow.AlleleInterpretation.allele_id).filter(
            workflow.AlleleInterpretation.user == user
        ).subquery()

        wf_allele_user = session.query(workflow.AlleleInterpretation).filter(
            workflow.AlleleInterpretation.allele_id.in_(sq_wf_allele_user),
            workflow.AlleleInterpretation.status != 'Not started'
        ).order_by(workflow.AlleleInterpretation.date_last_update).limit(20).all()

        sq_wf_analysis_user = session.query(workflow.AnalysisInterpretation.analysis_id).filter(
            workflow.AnalysisInterpretation.user == user
        ).subquery()

        wf_analysis_user = session.query(workflow.AnalysisInterpretation).filter(
            workflow.AnalysisInterpretation.analysis_id.in_(sq_wf_analysis_user),
            workflow.AnalysisInterpretation.status != 'Not started'
        ).order_by(workflow.AnalysisInterpretation.date_last_update).limit(20).all()

        # Create activity stream for user

        workflow_stream_objs = sorted(wf_allele_user + wf_analysis_user, key=lambda x: x.date_last_update)

        # Preload data
        stream_users = session.query(model_user.User).filter(
            model_user.User.id.in_([o.user_id for o in workflow_stream_objs])
        ).all()
        stream_users = schemas.UserSchema(strict=True).dump(stream_users, many=True).data

        genepanels = session.query(gene.Genepanel).filter(
            tuple_(gene.Genepanel.name, gene.Genepanel.version).in_([(o.genepanel_name, o.genepanel_version) for o in wf_allele_user])
        ).all()

        stream_alleles = session.query(allele.Allele).filter(
            allele.Allele.id.in_([o.allele_id for o in wf_allele_user])
        ).all()

        stream_analyses = session.query(sample.Analysis).filter(
            sample.Analysis.id.in_([o.analysis_id for o in wf_analysis_user])
        ).all()

        adl = AlleleDataLoader(session)

        workflow_stream = list()

        for obj in workflow_stream_objs:
            stream_obj = {
                'user': next(u for u in stream_users if u['id'] == obj.user_id),
                'date_last_update': obj.date_last_update.isoformat()
            }
            if isinstance(obj, workflow.AlleleInterpretation):
                stream_obj_allele = next(a for a in stream_alleles if a.id == obj.allele_id)
                stream_obj_genepanel = next(gp for gp in genepanels if gp.name == obj.genepanel_name and gp.version == obj.genepanel_version)
                # TODO: This can by optimized to preload in
                # batches per genepanel. Shouldn't matter too much.
                stream_obj['allele'] = adl.from_objs(
                    [stream_obj_allele],
                    genepanel=stream_obj_genepanel,
                    include_reference_assessments=False,
                    include_custom_annotation=False,
                    include_allele_report=False
                )
            elif isinstance(obj, workflow.AnalysisInterpretation):
                stream_obj_analysis = next(a for a in stream_analyses if a.id == obj.analysis_id)
                stream_obj['analysis'] = schemas.AnalysisSchema(strict=True).dump(stream_obj_analysis).data
            workflow_stream.append(stream_obj)

        return workflow_stream

