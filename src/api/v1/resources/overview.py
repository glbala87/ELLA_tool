import itertools
import datetime
import pytz
from collections import defaultdict
from sqlalchemy import func, tuple_, or_, and_
from sqlalchemy.orm import aliased
from vardb.datamodel import sample, workflow, assessment, allele, genotype, gene, user as model_user

from api import schemas, ApiError
from api.v1.resource import LogRequestResource
from api.util import queries
from api.util.util import authenticate, paginate
from api.util.allelefilter import AlleleFilter
from api.util.alleledataloader import AlleleDataLoader

from api.config import config


def load_genepanel_alleles(session, gp_allele_ids):
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

    all_allele_ids = list(itertools.chain.from_iterable(gp_allele_ids.values()))

    # Preload all alleles
    all_alleles = session.query(allele.Allele).filter(
        allele.Allele.id.in_(all_allele_ids)
    ).all()

    # Get display date
    allele_ids_deposit_date = dict()
    # Standalone alleles are not connected to analysis, and have no deposit date.
    # They do however have AlleleInterpretation objects with date_created.
    allele_ids_interpretation_deposit_date = session.query(workflow.AlleleInterpretation.allele_id, func.min(workflow.AlleleInterpretation.date_created)).filter(
        workflow.AlleleInterpretation.allele_id.in_(all_allele_ids)
    ).group_by(workflow.AlleleInterpretation.allele_id).all()
    allele_ids_deposit_date.update({k: v for k, v in allele_ids_interpretation_deposit_date})

    # Preload oldest analysis for each allele, to get the oldest datetime
    # for the analysis awaiting this allele's classification
    # If we have dates from both analysis and alleleinterpretation, we let oldest analysis take priority
    allele_ids_analysis_deposit_date = session.query(allele.Allele.id, func.min(sample.Analysis.deposit_date)).join(
        genotype.Genotype.alleles,
        sample.Sample,
        sample.Analysis
    ).filter(
        allele.Allele.id.in_(all_allele_ids)
    ).group_by(allele.Allele.id).all()
    allele_ids_deposit_date.update({k: v for k, v in allele_ids_analysis_deposit_date})

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
    ).order_by(
        workflow.AlleleInterpretation.date_last_update
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
    for gp_key, allele_ids in gp_allele_ids.iteritems():  # ('HBOC', 'v01'), [1, 2, 3, ...]

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
                'oldest_analysis': allele_ids_deposit_date[a['id']].isoformat(),
                'highest_analysis_priority': allele_ids_priority.get(a['id'], 1),  # If there's no analysis connected, set to normal priority
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
        raise RuntimeError("Missing required argument analysis_ids when analysis_allele_ids is provided.")

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

    :param session: database session
    :param alleleinterpretation_allele_ids: List of allele ids connected to AlleleInterpretations

    Returns a dict of format: {
        ('HBOC', 'v01'): set([1, 3, 4]),
        ('SomethingElse', 'v01'): set([1])
    }
    """

    alleleinterpretation_gp_allele_ids = defaultdict(set)
    allele_ids_genepanels = session.query(
        workflow.AlleleInterpretation.genepanel_name,
        workflow.AlleleInterpretation.genepanel_version,
        workflow.AlleleInterpretation.allele_id
    ).filter(
        workflow.AlleleInterpretation.allele_id.in_(alleleinterpretation_allele_ids)
    ).distinct()

    for entry in allele_ids_genepanels.all():
        alleleinterpretation_gp_allele_ids[(entry[0], entry[1])].add(entry[2])

    return alleleinterpretation_gp_allele_ids


def filter_result_of_alleles(session, allele_ids):

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
        allele.Allele.id.in_(allele_ids)
    ).all()

    # Make a dict of (gp_name, gp_version): [allele_ids] for use with AlleleFilter
    gp_allele_ids = defaultdict(list)
    for entry in allele_ids_genepanels:
        gp_allele_ids[(entry[0], entry[1])].append(entry[2])

    # Filter out alleles
    af = AlleleFilter(session)
    return af.filter_alleles(gp_allele_ids)  # gp_key => {allele ids distributed by filter status}


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
        alleleinterpretation_allele_ids = alleleinterpretation_allele_ids.slice(start, end)

    alleleinterpretation_allele_ids = alleleinterpretation_allele_ids.all()
    return alleleinterpretation_allele_ids, count


class OverviewAlleleResource(LogRequestResource):

    def _get_alleles_no_alleleassessment_notstarted_analysis(self, session, user=None):
        """
        Returns a list of (allele_ids, analysis_ids) that are missing alleleassessments.

        We only return allele_ids that:
            - Are connected to analyses that are 'Not started'.
            - Are missing valid alleleassessments (i.e not outdated if applicable)
            - Do not have an alleleinterpretation that is not 'Not started' (i.e. is ongoing or awaiting review)

        Returns (list of allele ids, list of analysis ids)
        """

        allele_filters = [
            allele.Allele.id.in_(queries.allele_ids_not_started_analyses(session)),  # Allele ids in not started analyses
            ~allele.Allele.id.in_(queries.allele_ids_with_valid_alleleassessments(session)),  # Allele ids without valid allele assessment
            ~allele.Allele.id.in_(queries.workflow_alleles_ongoing(session)),  # Allele ids part of ongoing alleleinterpretation
            ~allele.Allele.id.in_(queries.workflow_alleles_marked_review(session))  # Allele ids part of review alleleinterpretation
        ]
        if user is not None:
            allele_filters.append(
                allele.Allele.id.in_(queries.workflow_alleles_for_genepanels(session, user.group.genepanels))
            )

        allele_ids = session.query(allele.Allele.id).filter(
            *allele_filters
        ).all()

        allele_ids = [a[0] for a in allele_ids]

        analysis_ids = session.query(sample.Analysis.id).filter(
            sample.Analysis.id.in_(queries.workflow_analyses_not_started(session))
        )

        return allele_ids, analysis_ids

    def get_alleles_ongoing(self, session, user=None):
        """
        Returns alleles that are ongoing.

        If user argument is given, the alleles will be limited by user group's
        genepanels.
        """
        allele_filters = [allele.Allele.id.in_(queries.workflow_alleles_ongoing(session))]
        if user is not None:
            allele_filters.append(
                allele.Allele.id.in_(queries.workflow_alleles_for_genepanels(session, user.group.genepanels))
            )

        alleleinterpretation_allele_ids, count = get_alleles_existing_alleleinterpretation(
            session,
            and_(*allele_filters)
        )
        gp_allele_ids = get_alleleinterpretation_gp_allele_ids(
            session,
            alleleinterpretation_allele_ids
        )

        return load_genepanel_alleles(session, gp_allele_ids)

    def get_alleles_markedreview(self, session, user=None):
        """
        Returns alleles that are marked review.

        If user argument is given, the alleles will be limited by user group's
        genepanels.
        """
        allele_filters = [allele.Allele.id.in_(queries.workflow_alleles_marked_review(session))]
        if user is not None:
            allele_filters.append(
                allele.Allele.id.in_(queries.workflow_alleles_for_genepanels(session, user.group.genepanels))
            )

        alleleinterpretation_allele_ids, count = get_alleles_existing_alleleinterpretation(
            session,
            and_(*allele_filters)
        )

        gp_allele_ids = get_alleleinterpretation_gp_allele_ids(
            session,
            alleleinterpretation_allele_ids
        )

        return load_genepanel_alleles(session, gp_allele_ids)

    def get_alleles_not_started(self, session, user=None):
        """
        Returns alleles that are not started.

        If user argument is given, the alleles will be limited by user group's
        genepanels.

        For figuring out what counts as 'Not started',
        the following conditions are used:

        Take all alleles from all 'Not started' analyses:
           - subtract alleles with valid alleleassessment (i.e. exists and not outdated)
           - subtract alleles with ongoing/review alleleinterpretation
        Add all alleles from 'Not started' alleleinterpretation
        """
        analysis_allele_ids, analysis_ids = self._get_alleles_no_alleleassessment_notstarted_analysis(session, user)

        allele_filters = [allele.Allele.id.in_(queries.workflow_alleles_not_started(session))]
        if user is not None:
            allele_filters.append(
                allele.Allele.id.in_(queries.workflow_alleles_for_genepanels(session, user.group.genepanels))
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
        gp_nonfiltered_alleles = af.filter_alleles(analysis_gp_allele_ids)
        gp_allele_ids = {k: set(v['allele_ids']) for k, v in gp_nonfiltered_alleles.iteritems()}

        alleleinterpretation_gp_allele_ids = get_alleleinterpretation_gp_allele_ids(
            session,
            alleleinterpretation_allele_ids
        )

        for gp_key, allele_ids in alleleinterpretation_gp_allele_ids.iteritems():
            if gp_key not in gp_allele_ids:
                gp_allele_ids[gp_key] = set()
            gp_allele_ids[gp_key].update(allele_ids)

        return load_genepanel_alleles(session, gp_allele_ids)

    @authenticate()
    def get(self, session, user=None):
        return {
            'missing_alleleassessment': self.get_alleles_not_started(session, user=user),
            'marked_review': self.get_alleles_markedreview(session, user=user),
            'ongoing': self.get_alleles_ongoing(session, user=user)
        }


class OverviewAlleleFinalizedResource(LogRequestResource):

    @authenticate()
    @paginate
    def get(self, session, user=None, page=None, per_page=None):
        allele_filters = [allele.Allele.id.in_(queries.workflow_alleles_finalized(session))]
        if user is not None:
            allele_filters.append(
                allele.Allele.id.in_(queries.workflow_alleles_for_genepanels(session, user.group.genepanels))
            )

        alleleinterpretation_allele_ids, count = get_alleles_existing_alleleinterpretation(
            session,
            and_(*allele_filters),
            page=page,
            per_page=per_page
        )
        alleleinterpretation_allele_ids = [a[0] for a in alleleinterpretation_allele_ids]

        gp_allele_ids = get_alleleinterpretation_gp_allele_ids(
            session,
            alleleinterpretation_allele_ids
        )

        result = load_genepanel_alleles(session, gp_allele_ids)

        # Re-sort result, since the db queries in load_genepanel_alleles doesn't handle sorting
        result.sort(key=lambda x: alleleinterpretation_allele_ids.index(x['allele']['id']))
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


def _get_analysis_ids_for_user(session, user=None):
    analysis_ids_for_user = session.query(sample.Analysis.id)
    # Restrict analyses to analyses matching this user's group's genepanels
    if user is not None:
        analyses_for_genepanels = queries.workflow_analyses_for_genepanels(session, user.group.genepanels)
        analysis_ids_for_user = analysis_ids_for_user.filter(
            sample.Analysis.id.in_(analyses_for_genepanels)
        )
    return analysis_ids_for_user


def get_categorized_analyses(session, user=None):

    user_analysis_ids = _get_analysis_ids_for_user(session, user=user)

    categories = [
        ('not_started', queries.workflow_analyses_not_started(session)),
        ('marked_review', queries.workflow_analyses_marked_review(session)),
        ('ongoing', queries.workflow_analyses_ongoing(session))
    ]

    aschema = schemas.AnalysisFullSchema()
    final_analyses = dict()
    for key, subquery in categories:
        analyses = session.query(sample.Analysis).filter(
            sample.Analysis.id.in_(user_analysis_ids),
            sample.Analysis.id.in_(subquery),
        ).all()
        final_analyses[key] = aschema.dump(analyses, many=True).data

    return final_analyses


def get_finalized_analyses(session, user=None, page=None, per_page=None):

    user_analysis_ids = _get_analysis_ids_for_user(session, user=user)

    sorted_analysis_ids = session.query(
        sample.Analysis.id.label('analysis_id'),
        func.max(workflow.AnalysisInterpretation.date_last_update).label('max_date_last_update')
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
    return schemas.AnalysisFullSchema().dump(finalized_analyses.all(), many=True).data, count


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
    gp_nonfiltered_allele_ids = af.filter_alleles(gp_allele_ids)
    nonfiltered_allele_ids = set(itertools.chain.from_iterable([v['allele_ids'] for v in gp_nonfiltered_allele_ids.values()]))

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
    categorized_allele_ids = _categorize_allele_ids_findings(session, nonfiltered_allele_ids)
    for analysis_id, analysis_allele_ids in analysis_ids_allele_ids_map.iteritems():
        analysis_nonfiltered_allele_ids = analysis_allele_ids & nonfiltered_allele_ids
        analysis_filtered_allele_ids = analysis_allele_ids - analysis_nonfiltered_allele_ids
        analysis = next(a for a in not_started_analyses if a['id'] == analysis_id)

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
            raise ApiError("Allele was not categorized correctly. This may indicate a bug.")

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
        not_started_categories = categorize_analyses_by_findings(session, not_started_analyses)
        categorized_analyses.update({'not_started_' + k: v for k, v in not_started_categories.iteritems()})
        marked_review_analyses = categorized_analyses.pop('marked_review')
        marked_review_categories = categorize_analyses_by_findings(session, marked_review_analyses)
        categorized_analyses.update({'marked_review_' + k: v for k, v in marked_review_categories.iteritems()})
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


class OverviewActivitiesResource(LogRequestResource):

    @staticmethod
    def _get_start_end_action_workflow(session, model, model_id_field, model_objs):
        """
        Fetches the start and end action for provided interpretation model.

        :param session: SQLAlchemy session
        :param model: Either workflow.AlleleInterpretation or workflow.AnalysisInterpretation
        :param model_id_field: Field name for the connected object id, e.g. 'allele_id' or 'analysis_id'
        :param model_objs: The interpretation objects for which to get the actions.
        :returns: dict of {id: (start_action, end_action)}
        """

        obj_ids = [getattr(obj, model_id_field) for obj in model_objs]

        # Get all objects and their current status, sorted ascending (oldest first)
        status_order = session.query(
            # e.g. workflow.AlleleInterpretation.allele_id
            getattr(model, model_id_field),
            model.id,
            model.status,
            model.date_created,
        ).filter(
            # e.g. workflow.AlleleInterpretation.allele_id.in_(...)
            getattr(model, model_id_field).in_(obj_ids)
        ).order_by(
            model.date_created
        ).all()

        status = dict()  # {id: (start_action, end_action)}
        for obj in model_objs:
            obj_wfs = [w for w in status_order if w[0] == getattr(obj, model_id_field)]
            is_first = obj_wfs[0][1] == obj.id  # Was sorted oldest first above

            # Get start action
            start_action = None
            if is_first:
                # If our object is the first in the list (i.e. oldest),
                # we must have started a new workflow
                start_action = 'started'
            else:
                # If not first, then we are either doing
                # or have done a review
                if obj.status == 'Ongoing':
                    start_action = 'started_review'
                else:
                    start_action = 'review'

            # Get end action
            end_action = None
            if obj.end_action == 'Mark review':
                end_action = 'marked_review'
            elif obj.end_action == 'Finalize':
                end_action = 'finalized'
            status[obj.id] = (start_action, end_action)

        return status

    @staticmethod
    def _get_latest_workflows(session, model, model_id_field, user, limit=20):
        """
        Fetches {limit} latest interpretations for provided model.

        :param session: SQLAlchemy session
        :param model: Either workflow.AlleleInterpretation or workflow.AnalysisInterpretation
        :param model_id_field: Field name for the connected object id, e.g. 'allele_id' or 'analysis_id'
        :param user: User model object
        :returns: Objects of type {model}
        """
        sq_wf_for_user = session.query(getattr(model, model_id_field)).filter(
            model.user == user
        ).subquery()

        wf_latest = session.query(model).filter(
            getattr(model, model_id_field).in_(sq_wf_for_user),
            model.status != 'Not started'
        ).order_by(model.date_created.desc()).limit(limit).all()
        return wf_latest

    @authenticate()
    def get(self, session, user=None):
        """
        Provides dashboard data for authenticated user.
        """

        # Get latest workflows where the user has been involved
        wf_allele_user = OverviewActivitiesResource._get_latest_workflows(
            session,
            workflow.AlleleInterpretation,
            'allele_id',
            user
        )

        wf_analysis_user = OverviewActivitiesResource._get_latest_workflows(
            session,
            workflow.AnalysisInterpretation,
            'analysis_id',
            user
        )

        # Create activity stream for user
        workflow_stream_objs = sorted(wf_allele_user + wf_analysis_user, key=lambda x: x.date_last_update, reverse=True)

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

        # Get start/end actions for each workflow type
        wf_allele_actions = OverviewActivitiesResource._get_start_end_action_workflow(
            session,
            workflow.AlleleInterpretation,
            'allele_id',
            wf_allele_user
        )

        wf_analysis_actions = OverviewActivitiesResource._get_start_end_action_workflow(
            session,
            workflow.AnalysisInterpretation,
            'analysis_id',
            wf_analysis_user
        )

        adl = AlleleDataLoader(session)
        workflow_stream = list()

        for obj in workflow_stream_objs:
            stream_obj = {
                'user': next(u for u in stream_users if u['id'] == obj.user_id),
                'date_last_update': obj.date_last_update.isoformat()
            }
            if isinstance(obj, workflow.AlleleInterpretation):
                stream_obj['start_action'], stream_obj['end_action'] = wf_allele_actions.get(obj.id)
                stream_obj_allele = next(a for a in stream_alleles if a.id == obj.allele_id)
                stream_obj_genepanel = next(gp for gp in genepanels if gp.name == obj.genepanel_name and gp.version == obj.genepanel_version)
                stream_obj['allele'] = adl.from_objs(
                    [stream_obj_allele],
                    genepanel=stream_obj_genepanel,
                    include_reference_assessments=False,
                    include_custom_annotation=False,
                    include_allele_report=False
                )[0]
                stream_obj['genepanel'] = {
                    'name': stream_obj_genepanel.name,
                    'version': stream_obj_genepanel.version
                }
            elif isinstance(obj, workflow.AnalysisInterpretation):
                stream_obj['start_action'], stream_obj['end_action'] = wf_analysis_actions.get(obj.id)
                stream_obj_analysis = next(a for a in stream_analyses if a.id == obj.analysis_id)
                stream_obj['analysis'] = schemas.AnalysisSchema(strict=True).dump(stream_obj_analysis).data

            workflow_stream.append(stream_obj)

        return workflow_stream

