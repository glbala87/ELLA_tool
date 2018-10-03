import itertools
import datetime
import pytz
from collections import defaultdict
from sqlalchemy import func, tuple_, or_, and_, select
from sqlalchemy.orm import aliased, defer, joinedload
from vardb.datamodel import sample, workflow, assessment, allele, genotype, gene, user as model_user

from api import schemas, ApiError
from api.v1.resource import LogRequestResource
from api.allelefilter import AlleleFilter
from api.util import queries
from api.util.util import authenticate, paginate
from api.util.alleledataloader import AlleleDataLoader

from api.config import config


def load_genepanel_alleles(session, gp_allele_ids, analysis_ids=None):
    """
    Loads in allele data from AlleleDataLoader for all allele ids given by input structure:

    gp_allele_ids = {
        ('HBOC', 'v01'): [1, 2, 3, ...],
        ('HBOCutv', 'v01'): [1, 2, 3, ...],
    }

    analysis_ids is a list with ids from which to load connected data
    like priority and oldest date, in order to show whether any waiting
    analysis has high priority or is old.
    If empty, only information from AlleleInterpretation and InterpretationLog
    for the allele itself is used.

    Returns [
        {
            'genepanel': {...genepanel data...},
            'allele': {...allele data...},
            'oldest_analysis': '<dateisoformat>',
            'priority': <int>,
            'interpretations': [{...interpretation_data...}, ...]
        },
        ...
    ]
    """

    all_allele_ids = list(
        itertools.chain.from_iterable(gp_allele_ids.values()))

    # Preload all alleles
    all_alleles = session.query(allele.Allele).filter(
        allele.Allele.id.in_(all_allele_ids)
    ).all()

    # Get display date
    allele_ids_deposit_date = dict()
    # Standalone alleles are not connected to analysis, and have no deposit date.
    # They do however have AlleleInterpretation objects with date_created.
    allele_ids_interpretation_deposit_date = session.query(
        workflow.AlleleInterpretation.allele_id,
        func.min(workflow.AlleleInterpretation.date_created)
    ).filter(
        workflow.AlleleInterpretation.allele_id.in_(all_allele_ids)
    ).group_by(workflow.AlleleInterpretation.allele_id).all()
    allele_ids_deposit_date.update(
        {k: v for k, v in allele_ids_interpretation_deposit_date})

    # Preload oldest analysis for each allele, to get the oldest datetime
    # for the analysis awaiting this allele's classification
    # If we have dates from both analysis and alleleinterpretation, we let oldest analysis take priority
    if analysis_ids:
        allele_ids_analysis_deposit_date = session.query(
            allele.Allele.id,
            func.min(sample.Analysis.deposit_date)
        ).join(
            genotype.Genotype.alleles,
            sample.Sample,
            sample.Analysis
        ).filter(
            sample.Analysis.id.in_(analysis_ids),
            allele.Allele.id.in_(all_allele_ids)
        ).group_by(allele.Allele.id).all()
        allele_ids_deposit_date.update(
            {k: v for k, v in allele_ids_analysis_deposit_date}
        )

    # Preload interpretations for each allele
    allele_ids_interpretations = session.query(
        workflow.AlleleInterpretation
    ).options(
        defer('state'),
        defer('user_state')
    ).filter(
        workflow.AlleleInterpretation.allele_id.in_(all_allele_ids)
    ).order_by(
        workflow.AlleleInterpretation.date_last_update
    ).all()

    # Preload genepanels
    genepanels = session.query(gene.Genepanel).filter(
        tuple_(gene.Genepanel.name, gene.Genepanel.version).in_(
            gp_allele_ids.keys())
    ).all()

    # Load highest priority for each allele.
    # We get priority both from the highest priority of connected analyses,
    # as well as on the allele itself. The highest among them all are shown in UI.
    analysis_allele_ids_priority = {}

    if analysis_ids:
        analyses_priority = queries.workflow_analyses_priority(
            session,
            analysis_ids=analysis_ids
        ).subquery()

        analysis_allele_ids_priority = session.query(
            allele.Allele.id,
            func.max(func.coalesce(analyses_priority.c.priority, 1))
        ).join(
            genotype.Genotype.alleles,
            sample.Sample,
            sample.Analysis,
        ).outerjoin(
            analyses_priority,
            analyses_priority.c.analysis_id == sample.Analysis.id
        ).filter(
            allele.Allele.id.in_(all_allele_ids)
        ).group_by(allele.Allele.id).all()

        analysis_allele_ids_priority = {k: v for k, v in analysis_allele_ids_priority}

    allele_allele_ids_priority = queries.workflow_allele_priority(session).all()
    allele_allele_ids_priority = {k: v for k, v in allele_allele_ids_priority}

    # Load review comments

    allele_ids_review_comment = queries.workflow_allele_review_comment(session).all()
    allele_ids_review_comment = {k: v for k, v in allele_ids_review_comment}

    # Set structures/loaders
    final_alleles = list()
    adl = AlleleDataLoader(session)
    alleleinterpretation_schema = schemas.AlleleInterpretationOverviewSchema()

    # Create output data
    # ('HBOC', 'v01'), [1, 2, 3, ...]
    for gp_key, allele_ids in gp_allele_ids.iteritems():

        genepanel = next(g for g in genepanels if g.name ==
                         gp_key[0] and g.version == gp_key[1])
        gp_alleles = [a for a in all_alleles if a.id in allele_ids]

        loaded_genepanel_alleles = adl.from_objs(
            gp_alleles,
            genepanel=genepanel,
            include_allele_assessment=True,  # Display existing class in overview
            # Rest is extra data not needed for our use cases here
            include_custom_annotation=False,
            include_reference_assessments=False,
            include_allele_report=False,
            allele_assessment_schema=schemas.AlleleAssessmentOverviewSchema
        )

        for a in loaded_genepanel_alleles:
            interpretations = [
                i for i in allele_ids_interpretations if i.allele_id == a['id']]
            final_alleles.append({
                'genepanel': {'name': genepanel.name, 'version': genepanel.version},
                'allele': a,
                'oldest_analysis': allele_ids_deposit_date[a['id']].isoformat(),
                'priority': max([
                    analysis_allele_ids_priority.get(a['id'], 1),
                    allele_allele_ids_priority.get(a['id'], 1)
                ]),
                'review_comment': allele_ids_review_comment.get(a['id'], None),
                'interpretations': alleleinterpretation_schema.dump(interpretations, many=True).data
            })

    return final_alleles


def get_analysis_gp_allele_ids(session, analysis_allele_ids, analysis_ids, alleleinterpretation_allele_ids=None):
    """
    Creates a dictionary of genepanels and allele_ids as matched by analyses and/or
    alleleinterpretation.
    :param session: database session
    :param analysis_allele_ids: List of allele ids connected to analyses
    :param analysis_ids: List of analysis ids from which we should get genepanels.

    Returns a dict of format: {
        ('HBOC', 'v01'): set([1, 3, 4]),
        ('SomethingElse', 'v01'): set([1])
    }
    """
    if not analysis_ids:
        raise RuntimeError(
            "Missing required argument analysis_ids when analysis_allele_ids is provided.")

    analysis_gp_allele_ids = defaultdict(set)

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
        workflow.AnalysisInterpretation.analysis_id.in_(analysis_ids),
        workflow.AnalysisInterpretation.status == 'Not started',
        allele.Allele.id.in_(analysis_allele_ids)
    ).distinct().all()

    for entry in allele_ids_genepanels:
        analysis_gp_allele_ids[(entry[0], entry[1])].add(entry[2])

    return analysis_gp_allele_ids


def get_alleleinterpretation_gp_allele_ids(session, alleleinterpretation_allele_ids):
    """
    Creates a dictionary of genepanels and allele_ids as matched provided alleleinterpretationids.

    Only select the latest interpretation for each allele_id to avoid fetching multiple genepanels
    as they can differ between the interpretations.

    :param session: database session
    :param alleleinterpretation_allele_ids: List of allele ids connected to AlleleInterpretations

    Returns a dict of format: {
        ('HBOC', 'v01'): set([1, 3, 4]),
        ('SomethingElse', 'v01'): set([2])
    }
    """

    alleleinterpretation_gp_allele_ids = defaultdict(set)

    latest_interpretation = session.query(
        workflow.AlleleInterpretation.id
    ).order_by(
        workflow.AlleleInterpretation.allele_id,
        workflow.AlleleInterpretation.date_last_update.desc(),
    ).distinct(
        workflow.AlleleInterpretation.allele_id  # DISTINCT ON
    ).subquery()

    allele_ids_genepanels = session.query(
        workflow.AlleleInterpretation.genepanel_name,
        workflow.AlleleInterpretation.genepanel_version,
        workflow.AlleleInterpretation.allele_id
    ).filter(
        workflow.AlleleInterpretation.allele_id.in_(alleleinterpretation_allele_ids),
        workflow.AlleleInterpretation.id == latest_interpretation.c.id
    ).distinct()

    for entry in allele_ids_genepanels.all():
        alleleinterpretation_gp_allele_ids[(entry[0], entry[1])].add(entry[2])

    return alleleinterpretation_gp_allele_ids


def get_alleles_existing_alleleinterpretation(session, allele_filter, user=None, page=None, per_page=None):
    """
    Returns allele_ids that has connected AlleleInterpretations,
    given allele_filter from argument.

    Supports pagination.
    """

    # Apply filter using Allele table as base
    allele_ids = session.query(allele.Allele.id).filter(
        allele_filter
    )

    # Now get the ones that are actually connected to AlleleInterpretation
    # (distinct allele_ids sorted by date_last_update)
    alleleinterpretation_allele_ids = session.query(
        workflow.AlleleInterpretation.allele_id
    ).filter(
        workflow.AlleleInterpretation.allele_id.in_(allele_ids)
    ).group_by(
        workflow.AlleleInterpretation.allele_id
    ).order_by(
        func.max(workflow.AlleleInterpretation.date_last_update).desc()
    )

    count = alleleinterpretation_allele_ids.count()

    if page and per_page:
        start = (page - 1) * per_page
        end = page * per_page
        alleleinterpretation_allele_ids = alleleinterpretation_allele_ids.slice(
            start, end)

    alleleinterpretation_allele_ids = alleleinterpretation_allele_ids.all()
    return alleleinterpretation_allele_ids, count


class OverviewAlleleResource(LogRequestResource):

    def _get_not_started_analysis_ids(self, session):
        """
        Returns analysis ids for relevant not started analysis workflows.
        """
        return session.query(sample.Analysis.id).filter(
            or_(
                sample.Analysis.id.in_(
                    queries.workflow_analyses_interpretation_not_started(session)),
                sample.Analysis.id.in_(
                    queries.workflow_analyses_notready_not_started(session))
            )
        )

    def _get_alleles_no_alleleassessment_notstarted_analysis(self, session, user=None):
        """
        Returns a list of (allele_ids, analysis_ids) that are missing alleleassessments.

        We only return allele_ids that:
            - Are connected to analyses that are 'Not started' (having 'Not ready' or 'Interpretation' as workflow status).
            - Are missing valid alleleassessments (i.e not outdated if applicable)
            - Is not Ongoing or is waiting for Review

        Returns (list of allele ids, list of analysis ids)
        """

        # Using subqueries makes PostgreSQL perform terribly due to bad planning.
        # Instead, use CTE which acts like optimization fences, preventing PostgreSQL from optimizing the query.
        # In our case this makes the query go from several seconds to a few milliseconds.
        allele_ids_not_started = queries.allele_ids_not_started_analyses(session).cte('not_started')
        allele_ids_valid_alleleassessments = queries.allele_ids_with_valid_alleleassessments(session).cte('valid_alleleassessments')
        allele_ids_review = queries.workflow_alleles_review_not_started(session).cte('review')
        allele_ids_ongoing = queries.workflow_alleles_ongoing(session).cte('ongoing')

        allele_filters = [
            # Allele ids in not started analyses
            allele.Allele.id.in_(select([allele_ids_not_started.c.id])),
            # Exclude allele ids with valid alleleassessment
            ~allele.Allele.id.in_(select([allele_ids_valid_alleleassessments.c.id])),
            # Exclude alleles that would show under Review section
            ~allele.Allele.id.in_(select([allele_ids_review.c.allele_id])),
            # Exclude alleles that are Ongoing
            ~allele.Allele.id.in_(select([allele_ids_ongoing.c.allele_id]))
        ]

        if user is not None:
            allele_filters.append(
                allele.Allele.id.in_(queries.workflow_alleles_for_genepanels(
                    session, user.group.genepanels))
            )

        allele_ids = session.query(allele.Allele.id).filter(
            *allele_filters
        ).all()

        allele_ids = [a[0] for a in allele_ids]

        return allele_ids

    def get_alleles_for_status(self, session, status, user=None):
        """
        Returns alleles for a given status.

        If user argument is given, the alleles will be limited by user group's
        genepanels.
        """

        status_queries = {
            'Ongoing': queries.workflow_alleles_ongoing,
            'Review': queries.workflow_alleles_review_not_started,
        }

        allele_filters = [allele.Allele.id.in_(
            status_queries[status](session))]
        if user is not None:
            allele_filters.append(
                allele.Allele.id.in_(queries.workflow_alleles_for_genepanels(
                    session, user.group.genepanels))
            )

        alleleinterpretation_allele_ids, count = get_alleles_existing_alleleinterpretation(
            session,
            and_(*allele_filters)
        )

        gp_allele_ids = get_alleleinterpretation_gp_allele_ids(
            session,
            alleleinterpretation_allele_ids
        )

        analysis_ids = self._get_not_started_analysis_ids(session)
        return load_genepanel_alleles(session, gp_allele_ids, analysis_ids=analysis_ids)

    def get_alleles_not_started(self, session, user=None):
        """
        Returns alleles that are not started.

        If user argument is given, the alleles will be limited by user group's
        genepanels.

        For figuring out what counts as 'Not started',
        the following conditions are used:

        Take all alleles from all 'Not started' analyses in 'Interpretation' or 'Not ready' workflow status:
           - subtract alleles with valid alleleassessment (i.e. exists and not outdated)
           - subtract alleles with ongoing/review alleleinterpretation
        Add all alleles from 'Not started' alleleinterpretation
        """
        analysis_allele_ids = self._get_alleles_no_alleleassessment_notstarted_analysis(session, user)
        analysis_ids = self._get_not_started_analysis_ids(session)

        allele_filters = [allele.Allele.id.in_(
            queries.workflow_alleles_interpretation_not_started(session))]
        if user is not None:
            allele_filters.append(
                allele.Allele.id.in_(queries.workflow_alleles_for_genepanels(
                    session, user.group.genepanels))
            )

        alleleinterpretation_allele_ids = get_alleles_existing_alleleinterpretation(
            session,
            and_(*allele_filters)
        )[0]

        analysis_gp_allele_ids = get_analysis_gp_allele_ids(
            session,
            analysis_allele_ids,
            analysis_ids,
        )

        # Filter analysis allele ids
        af = AlleleFilter(session)
        gp_nonfiltered_alleles, _ = af.filter_alleles(analysis_gp_allele_ids, None)
        gp_allele_ids = {k: set(v['allele_ids'])
                         for k, v in gp_nonfiltered_alleles.iteritems()}

        alleleinterpretation_gp_allele_ids = get_alleleinterpretation_gp_allele_ids(
            session,
            alleleinterpretation_allele_ids
        )

        # Add alleleinterpretation allele_ids to analysis' allele_ids
        for gp_key, allele_ids in alleleinterpretation_gp_allele_ids.iteritems():
            if gp_key not in gp_allele_ids:
                gp_allele_ids[gp_key] = set()
            gp_allele_ids[gp_key].update(allele_ids)

        return load_genepanel_alleles(session, gp_allele_ids, analysis_ids=analysis_ids)

    @authenticate()
    def get(self, session, user=None):
        return {
            'missing_alleleassessment': self.get_alleles_not_started(session, user=user),
            'marked_review': self.get_alleles_for_status(session, 'Review', user=user),
            'ongoing': self.get_alleles_for_status(session, 'Ongoing', user=user),
        }


class OverviewAlleleFinalizedResource(LogRequestResource):

    @authenticate()
    @paginate
    def get(self, session, user=None, page=None, per_page=None):
        allele_filters = [allele.Allele.id.in_(
            queries.workflow_alleles_finalized(session))]
        if user is not None:
            allele_filters.append(
                allele.Allele.id.in_(queries.workflow_alleles_for_genepanels(
                    session, user.group.genepanels))
            )

        alleleinterpretation_allele_ids, count = get_alleles_existing_alleleinterpretation(
            session,
            and_(*allele_filters),
            page=page,
            per_page=per_page
        )
        alleleinterpretation_allele_ids = [a[0]
                                           for a in alleleinterpretation_allele_ids]

        gp_allele_ids = get_alleleinterpretation_gp_allele_ids(
            session,
            alleleinterpretation_allele_ids
        )

        result = load_genepanel_alleles(session, gp_allele_ids)

        # Re-sort result, since the db queries in load_genepanel_alleles doesn't handle sorting
        result.sort(key=lambda x: alleleinterpretation_allele_ids.index(
            x['allele']['id']))
        return result, count


def _categorize_allele_ids_findings(session, allele_ids):
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
    classification_findings = [o['value'] for o in classification_options if o.get(
        'include_analysis_with_findings')]
    classification_wo_findings = [o['value'] for o in classification_options if not o.get(
        'include_analysis_with_findings')]

    categorized_allele_ids = {

        'with_findings': session.query(assessment.AlleleAssessment.allele_id).filter(
            assessment.AlleleAssessment.allele_id.in_(allele_ids),
            assessment.AlleleAssessment.classification.in_(
                classification_findings),
            *queries.valid_alleleassessments_filter(session)
        ).all(),

        'without_findings': session.query(assessment.AlleleAssessment.allele_id).filter(
            assessment.AlleleAssessment.allele_id.in_(allele_ids),
            assessment.AlleleAssessment.classification.in_(
                classification_wo_findings),
            *queries.valid_alleleassessments_filter(session)
        ).all(),

        'missing_alleleassessments': session.query(allele.Allele.id).outerjoin(assessment.AlleleAssessment).filter(
            allele.Allele.id.in_(allele_ids),
            or_(
                # outerjoin() gives null values when missing alleleassessment
                assessment.AlleleAssessment.allele_id.is_(None),
                # Include cases where classification isn't valid anymore (notice inversion operator)
                ~and_(*queries.valid_alleleassessments_filter(session))
            ),
            # The filter below is part of the queries.valid_alleleassessments_filter above.
            # Since we negate that query, we end up including all alleleassessment that are superceeded.
            # We therefore need to explicitly exclude those here.
            assessment.AlleleAssessment.date_superceeded.is_(None)
        ).all()
    }

    # Strip out the tuples from db results and convert to set()
    categorized_allele_ids = {k: set([a[0] for a in v])
                              for k, v in categorized_allele_ids.iteritems()}
    return categorized_allele_ids


def _get_analysis_ids_for_user(session, user=None):
    analysis_ids_for_user = session.query(sample.Analysis.id)
    # Restrict analyses to analyses matching this user's group's genepanels
    if user is not None:
        analyses_for_genepanels = queries.workflow_analyses_for_genepanels(
            session, user.group.genepanels)
        analysis_ids_for_user = analysis_ids_for_user.filter(
            sample.Analysis.id.in_(analyses_for_genepanels)
        )
    return analysis_ids_for_user


def get_categorized_analyses(session, user=None):

    user_analysis_ids = _get_analysis_ids_for_user(session, user=user)

    categories = [
        ('not_ready', queries.workflow_analyses_notready_not_started(session)),
        ('not_started', queries.workflow_analyses_interpretation_not_started(session)),
        ('marked_review', queries.workflow_analyses_review_not_started(session)),
        ('marked_medicalreview',
         queries.workflow_analyses_medicalreview_not_started(session)),
        ('ongoing', queries.workflow_analyses_ongoing(session))
    ]

    aschema = schemas.AnalysisSchema()
    final_analyses = dict()
    for key, subquery in categories:
        analyses = session.query(
            sample.Analysis
        ).options(
            joinedload(sample.Analysis.interpretations).defer('state').defer('user_state')
        ).filter(
            sample.Analysis.id.in_(user_analysis_ids),
            sample.Analysis.id.in_(subquery),
        ).all()
        final_analyses[key] = aschema.dump(analyses, many=True).data

        # Load in priority, warning_cleared and review_comment
        analysis_ids = [a.id for a in analyses]
        priorities = queries.workflow_analyses_priority(session, analysis_ids)
        review_comments = queries.workflow_analyses_review_comment(session, analysis_ids)
        warnings_cleared = queries.workflow_analyses_warning_cleared(session, analysis_ids)

        for analysis in final_analyses[key]:
            priority = next((p.priority for p in priorities if p.analysis_id == analysis['id']), 1)
            analysis['priority'] = priority
            review_comment = next((rc.review_comment for rc in review_comments if rc.analysis_id == analysis['id']), None)
            if review_comment:
                analysis['review_comment'] = review_comment
            warning_cleared = next((wc.warning_cleared for wc in warnings_cleared if wc.analysis_id == analysis['id']), None)
            if warning_cleared:
                analysis['warning_cleared'] = warning_cleared

    return final_analyses


def get_finalized_analyses(session, user=None, page=None, per_page=None):

    user_analysis_ids = _get_analysis_ids_for_user(session, user=user)

    sorted_analysis_ids = session.query(
        sample.Analysis.id.label('analysis_id'),
        func.max(workflow.AnalysisInterpretation.date_last_update).label(
            'max_date_last_update')
    ).join(
        workflow.AnalysisInterpretation
    ).filter(
        sample.Analysis.id.in_(queries.workflow_analyses_finalized(session)),
        sample.Analysis.id.in_(user_analysis_ids)
    ).group_by(
        sample.Analysis.id
    ).subquery()

    # We need to give a hint to sqlalchemy to use the query's analysis
    # instead of the subquery's 'sample.Analysis' in the join
    new_analysis = aliased(sample.Analysis)
    finalized_analyses = session.query(new_analysis).join(
        sorted_analysis_ids, new_analysis.id == sorted_analysis_ids.c.analysis_id
    ).order_by(
        sorted_analysis_ids.c.max_date_last_update.desc()
    )
    count = finalized_analyses.count()

    if page and per_page:
        start = (page-1) * per_page
        end = page * per_page
        finalized_analyses = finalized_analyses.slice(start, end)
    return schemas.AnalysisSchema().dump(finalized_analyses.all(), many=True).data, count


def categorize_analyses_by_findings(session, not_started_analyses):

    # Get all (analysis_id, allele_id) combinations for input analyses.
    # We want to categorize these analyses into with_findings, without_findings and missing_alleleassessments
    # based on the state of their alleles' alleleassessments

    analysis_ids = [a['id'] for a in not_started_analyses]

    analysis_ids_allele_ids = session.query(sample.Analysis.id, allele.Allele.id).join(
        genotype.Genotype.alleles,
        sample.Sample,
        sample.Analysis,
    ).filter(
        sample.Analysis.id.in_(analysis_ids)
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
        workflow.AnalysisInterpretation.analysis_id.in_(analysis_ids),
        allele.Allele.id.in_(all_allele_ids)
    ).distinct().all()

    # Make a dict of (gp_name, gp_version): [allele_ids] for use with AlleleFilter
    gp_allele_ids = defaultdict(list)
    for entry in allele_ids_genepanels:
        gp_allele_ids[(entry[0], entry[1])].append(entry[2])

    # Filter out alleles
    af = AlleleFilter(session)
    gp_nonfiltered_allele_ids, _ = af.filter_alleles(gp_allele_ids, None)
    nonfiltered_allele_ids = set(itertools.chain.from_iterable(
        [v['allele_ids'] for v in gp_nonfiltered_allele_ids.values()]))

    # Now we can start to check our analyses and categorize them
    # First, sort into {analysis_id: [allele_ids]}
    analysis_ids_allele_ids_map = defaultdict(set)
    for a in analysis_ids_allele_ids:
        analysis_ids_allele_ids_map[a[0]].add(a[1])

    categories = {
        'with_findings': [],
        'without_findings': [],
        'missing_alleleassessments': []
    }

    # Next, compare the allele ids for each analysis and see which category they end up in
    # with regards to the categorized_allele_ids we created earlier.
    # Working with sets only for simplicity (& is intersection, < is subset)
    categorized_allele_ids = _categorize_allele_ids_findings(
        session, nonfiltered_allele_ids)
    for analysis_id, analysis_allele_ids in analysis_ids_allele_ids_map.iteritems():
        analysis_nonfiltered_allele_ids = analysis_allele_ids & nonfiltered_allele_ids
        analysis_filtered_allele_ids = analysis_allele_ids - analysis_nonfiltered_allele_ids
        analysis = next(
            a for a in not_started_analyses if a['id'] == analysis_id)

        # One or more allele is missing alleleassessment
        if analysis_nonfiltered_allele_ids & categorized_allele_ids['missing_alleleassessments']:
            categories['missing_alleleassessments'].append(analysis)
        # One or more allele has a finding
        elif analysis_nonfiltered_allele_ids & categorized_allele_ids['with_findings']:
            categories['with_findings'].append(analysis)
        # All alleles are without findings
        # Special case: All alleles were filtered out. Treat as without_findings.
        elif ((analysis_nonfiltered_allele_ids and
                analysis_nonfiltered_allele_ids <= categorized_allele_ids['without_findings']) or
                analysis_allele_ids == analysis_filtered_allele_ids):
            categories['without_findings'].append(analysis)
        # All possible cases should have been taken care of above
        else:
            raise ApiError(
                "Allele was not categorized correctly. This may indicate a bug.")

    return categories


class OverviewAnalysisFinalizedResource(LogRequestResource):

    @authenticate()
    @paginate
    def get(self, session, user=None, page=None, per_page=None):
        return get_finalized_analyses(session, user=user, page=page, per_page=per_page)


class OverviewAnalysisResource(LogRequestResource):

    @authenticate()
    def get(self, session, user=None):
        return get_categorized_analyses(session, user=user)


class OverviewAnalysisByFindingsResource(LogRequestResource):

    @authenticate()
    def get(self, session, user=None):
        categorized_analyses = get_categorized_analyses(session, user=user)
        not_started_analyses = categorized_analyses.pop('not_started')
        not_started_categories = categorize_analyses_by_findings(
            session, not_started_analyses)
        categorized_analyses.update(
            {'not_started_' + k: v for k, v in not_started_categories.iteritems()})
        marked_review_analyses = categorized_analyses.pop('marked_review')
        marked_review_categories = categorize_analyses_by_findings(
            session, marked_review_analyses)
        categorized_analyses.update(
            {'marked_review_' + k: v for k, v in marked_review_categories.iteritems()})
        return categorized_analyses


class OverviewUserStatsResource(LogRequestResource):

    @authenticate()
    def get(self, session, user=None):

        stats = dict()

        stats['analyses_cnt'] = session.query(sample.Analysis).join(
            workflow.AnalysisInterpretation
        ).filter(
            workflow.AnalysisInterpretation.user_id == user.id
        ).distinct().count()

        stats['alleles_cnt'] = session.query(allele.Allele).join(
            workflow.AlleleInterpretation
        ).filter(
            workflow.AlleleInterpretation.user_id == user.id
        ).distinct().count()

        return stats
