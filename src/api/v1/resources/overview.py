import itertools
from collections import defaultdict
from sqlalchemy import func, tuple_, or_, and_, select
from sqlalchemy.orm import defer
from vardb.datamodel import sample, workflow, allele, genotype, gene

from datalayer import AlleleFilter, AlleleDataLoader, queries
from datalayer.workflowcategorization import (
    get_categorized_analyses,
    get_finalized_analyses,
    categorize_analyses_by_findings,
)
from api import schemas, ApiError
from api.v1.resource import LogRequestResource
from api.util.util import authenticate, paginate


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

    all_allele_ids = list(itertools.chain.from_iterable(list(gp_allele_ids.values())))

    # Preload all alleles
    all_alleles = session.query(allele.Allele).filter(allele.Allele.id.in_(all_allele_ids)).all()

    # Get display date
    allele_ids_date = dict()
    # Standalone alleles are not connected to analysis, and have no requested or deposited date.
    # They do however have AlleleInterpretation objects with date_created.
    allele_ids_interpretation_date = (
        session.query(
            workflow.AlleleInterpretation.allele_id,
            func.min(workflow.AlleleInterpretation.date_created),
        )
        .filter(workflow.AlleleInterpretation.allele_id.in_(all_allele_ids))
        .group_by(workflow.AlleleInterpretation.allele_id)
        .all()
    )
    allele_ids_date.update({k: v for k, v in allele_ids_interpretation_date})

    # Preload oldest analysis for each allele, to get the oldest datetime
    # for the analysis awaiting this allele's classification
    # If we have dates from both analysis and alleleinterpretation, we let oldest analysis take priority
    if analysis_ids:
        allele_ids_analysis_date = (
            session.query(
                allele.Allele.id,
                func.min(
                    func.coalesce(sample.Analysis.date_requested, sample.Analysis.date_deposited)
                ),
            )
            .join(genotype.Genotype.alleles, sample.Sample, sample.Analysis)
            .filter(sample.Analysis.id.in_(analysis_ids), allele.Allele.id.in_(all_allele_ids))
            .group_by(allele.Allele.id)
            .all()
        )

        allele_ids_date.update({k: v for k, v in allele_ids_analysis_date})

    # Preload interpretations for each allele
    allele_ids_interpretations = (
        session.query(workflow.AlleleInterpretation)
        .options(defer("state"), defer("user_state"))
        .filter(workflow.AlleleInterpretation.allele_id.in_(all_allele_ids))
        .order_by(workflow.AlleleInterpretation.date_last_update)
        .all()
    )

    # Preload genepanels
    genepanels = (
        session.query(gene.Genepanel)
        .filter(tuple_(gene.Genepanel.name, gene.Genepanel.version).in_(list(gp_allele_ids.keys())))
        .all()
    )

    # Load highest priority for each allele.
    # We get priority both from the highest priority of connected analyses,
    # as well as on the allele itself. The highest among them all are shown in UI.
    analysis_allele_ids_priority = {}

    if analysis_ids:
        analyses_priority = queries.workflow_analyses_priority(
            session, analysis_ids=analysis_ids
        ).subquery()

        analysis_allele_ids_priority = (
            session.query(
                allele.Allele.id, func.max(func.coalesce(analyses_priority.c.priority, 1))
            )
            .join(genotype.Genotype.alleles, sample.Sample, sample.Analysis)
            .outerjoin(analyses_priority, analyses_priority.c.analysis_id == sample.Analysis.id)
            .filter(allele.Allele.id.in_(all_allele_ids))
            .group_by(allele.Allele.id)
            .all()
        )

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
    for gp_key, allele_ids in sorted(gp_allele_ids.items(), key=lambda x: x[0]):
        genepanel = next(g for g in genepanels if g.name == gp_key[0] and g.version == gp_key[1])
        gp_alleles = [a for a in all_alleles if a.id in allele_ids]

        loaded_genepanel_alleles = adl.from_objs(
            gp_alleles,
            genepanel=genepanel,
            include_allele_assessment=True,  # Display existing class in overview
            # Rest is extra data not needed for our use cases here
            include_custom_annotation=False,
            include_reference_assessments=False,
            include_allele_report=False,
            allele_assessment_schema=schemas.AlleleAssessmentOverviewSchema,
        )

        for a in loaded_genepanel_alleles:
            interpretations = [i for i in allele_ids_interpretations if i.allele_id == a["id"]]
            dumped_interpretations = [
                alleleinterpretation_schema.dump(i).data for i in interpretations
            ]
            final_alleles.append(
                {
                    "genepanel": {"name": genepanel.name, "version": genepanel.version},
                    "allele": a,
                    "oldest_analysis": allele_ids_date[a["id"]].isoformat(),
                    "priority": max(
                        [
                            analysis_allele_ids_priority.get(a["id"], 1),
                            allele_allele_ids_priority.get(a["id"], 1),
                        ]
                    ),
                    "review_comment": allele_ids_review_comment.get(a["id"], None),
                    "interpretations": dumped_interpretations,
                }
            )

    return final_alleles


def get_analysis_gp_allele_ids(
    session, analysis_allele_ids, analysis_ids, alleleinterpretation_allele_ids=None
):
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
            "Missing required argument analysis_ids when analysis_allele_ids is provided."
        )

    analysis_gp_allele_ids = defaultdict(set)

    allele_ids_genepanels = (
        session.query(
            workflow.AnalysisInterpretation.genepanel_name,
            workflow.AnalysisInterpretation.genepanel_version,
            allele.Allele.id,
        )
        .join(genotype.Genotype.alleles, sample.Sample, sample.Analysis)
        .filter(
            workflow.AnalysisInterpretation.analysis_id == sample.Analysis.id,
            workflow.AnalysisInterpretation.analysis_id.in_(analysis_ids),
            workflow.AnalysisInterpretation.status == "Not started",
            allele.Allele.id.in_(analysis_allele_ids),
        )
        .distinct()
        .all()
    )

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

    latest_interpretation = (
        session.query(workflow.AlleleInterpretation.id)
        .order_by(
            workflow.AlleleInterpretation.allele_id,
            workflow.AlleleInterpretation.date_last_update.desc(),
        )
        .distinct(workflow.AlleleInterpretation.allele_id)  # DISTINCT ON
        .subquery()
    )

    allele_ids_genepanels = (
        session.query(
            workflow.AlleleInterpretation.genepanel_name,
            workflow.AlleleInterpretation.genepanel_version,
            workflow.AlleleInterpretation.allele_id,
        )
        .filter(
            workflow.AlleleInterpretation.allele_id.in_(alleleinterpretation_allele_ids),
            workflow.AlleleInterpretation.id == latest_interpretation.c.id,
        )
        .distinct()
    )

    for entry in allele_ids_genepanels.all():
        alleleinterpretation_gp_allele_ids[(entry[0], entry[1])].add(entry[2])

    return alleleinterpretation_gp_allele_ids


def get_alleles_existing_alleleinterpretation(
    session, allele_filter, user=None, page=None, per_page=None
):
    """
    Returns allele_ids that has connected AlleleInterpretations,
    given allele_filter from argument.

    Supports pagination.
    """

    # Apply filter using Allele table as base
    allele_ids = session.query(allele.Allele.id).filter(allele_filter)

    # Now get the ones that are actually connected to AlleleInterpretation
    # (distinct allele_ids sorted by date_last_update)
    alleleinterpretation_allele_ids = (
        session.query(workflow.AlleleInterpretation.allele_id)
        .filter(workflow.AlleleInterpretation.allele_id.in_(allele_ids))
        .group_by(workflow.AlleleInterpretation.allele_id)
        .order_by(func.max(workflow.AlleleInterpretation.date_last_update).desc())
    )

    count = alleleinterpretation_allele_ids.count()

    if page and per_page:
        start = (page - 1) * per_page
        end = page * per_page
        alleleinterpretation_allele_ids = alleleinterpretation_allele_ids.slice(start, end)

    alleleinterpretation_allele_ids = alleleinterpretation_allele_ids.all()
    return alleleinterpretation_allele_ids, count


class OverviewAlleleResource(LogRequestResource):
    def _get_not_started_analysis_ids(self, session, genepanels):
        """
        Returns analysis ids for relevant not started analysis workflows.
        """
        return session.query(sample.Analysis.id).filter(
            or_(
                sample.Analysis.id.in_(
                    queries.workflow_analyses_interpretation_not_started(session)
                ),
                sample.Analysis.id.in_(queries.workflow_analyses_notready_not_started(session)),
            ),
            sample.Analysis.id.in_(queries.workflow_analyses_for_genepanels(session, genepanels)),
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
        allele_ids_not_started = queries.allele_ids_not_started_analyses(session).cte("not_started")
        allele_ids_valid_alleleassessments = queries.allele_ids_with_valid_alleleassessments(
            session
        ).cte("valid_alleleassessments")
        allele_ids_review = queries.workflow_alleles_review_not_started(session).cte("review")
        allele_ids_ongoing = queries.workflow_alleles_ongoing(session).cte("ongoing")

        allele_filters = [
            # Allele ids in not started analyses
            allele.Allele.id.in_(select([allele_ids_not_started.c.id])),
            # Exclude allele ids with valid alleleassessment
            ~allele.Allele.id.in_(select([allele_ids_valid_alleleassessments.c.id])),
            # Exclude alleles that would show under Review section
            ~allele.Allele.id.in_(select([allele_ids_review.c.allele_id])),
            # Exclude alleles that are Ongoing
            ~allele.Allele.id.in_(select([allele_ids_ongoing.c.allele_id])),
        ]

        if user is not None:
            allele_filters.append(
                allele.Allele.id.in_(
                    queries.workflow_alleles_for_genepanels(session, user.group.genepanels)
                )
            )

        allele_ids = session.query(allele.Allele.id).filter(*allele_filters).all()

        allele_ids = [a[0] for a in allele_ids]

        return allele_ids

    def get_alleles_for_status(self, session, status, user=None):
        """
        Returns alleles for a given status.

        If user argument is given, the alleles will be limited by user group's
        genepanels.
        """

        status_queries = {
            "Ongoing": queries.workflow_alleles_ongoing,
            "Review": queries.workflow_alleles_review_not_started,
        }

        allele_filters = [allele.Allele.id.in_(status_queries[status](session))]
        if user is not None:
            allele_filters.append(
                allele.Allele.id.in_(
                    queries.workflow_alleles_for_genepanels(session, user.group.genepanels)
                )
            )

        alleleinterpretation_allele_ids, count = get_alleles_existing_alleleinterpretation(
            session, and_(*allele_filters)
        )

        gp_allele_ids = get_alleleinterpretation_gp_allele_ids(
            session, alleleinterpretation_allele_ids
        )

        analysis_ids = self._get_not_started_analysis_ids(session, user.group.genepanels)
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
        analysis_allele_ids = self._get_alleles_no_alleleassessment_notstarted_analysis(
            session, user
        )
        analysis_ids = self._get_not_started_analysis_ids(session, user.group.genepanels)

        allele_filters = [
            allele.Allele.id.in_(queries.workflow_alleles_interpretation_not_started(session))
        ]
        if user is not None:
            allele_filters.append(
                allele.Allele.id.in_(
                    queries.workflow_alleles_for_genepanels(session, user.group.genepanels)
                )
            )

        alleleinterpretation_allele_ids = get_alleles_existing_alleleinterpretation(
            session, and_(*allele_filters)
        )[0]

        analysis_gp_allele_ids = get_analysis_gp_allele_ids(
            session, analysis_allele_ids, analysis_ids
        )

        # Filter analysis allele ids
        filterconfigs = queries.get_valid_filter_configs(session, user.group_id)

        if filterconfigs.count() != 1:
            raise ApiError(
                "Unable to find single filter config appropriate for overview filtering. Found {} filterconfigs.".format(
                    filterconfigs.count()
                )
            )

        filterconfig_id = filterconfigs.one().id

        af = AlleleFilter(session)
        gp_nonfiltered_alleles = af.filter_alleles(filterconfig_id, analysis_gp_allele_ids)
        gp_allele_ids = {k: set(v["allele_ids"]) for k, v in gp_nonfiltered_alleles.items()}

        alleleinterpretation_gp_allele_ids = get_alleleinterpretation_gp_allele_ids(
            session, alleleinterpretation_allele_ids
        )

        # Add alleleinterpretation allele_ids to analysis' allele_ids
        for gp_key, allele_ids in alleleinterpretation_gp_allele_ids.items():
            if gp_key not in gp_allele_ids:
                gp_allele_ids[gp_key] = set()
            gp_allele_ids[gp_key].update(allele_ids)

        return load_genepanel_alleles(session, gp_allele_ids, analysis_ids=analysis_ids)

    @authenticate()
    def get(self, session, user=None):
        return {
            "missing_alleleassessment": self.get_alleles_not_started(session, user=user),
            "marked_review": self.get_alleles_for_status(session, "Review", user=user),
            "ongoing": self.get_alleles_for_status(session, "Ongoing", user=user),
        }


class OverviewAlleleFinalizedResource(LogRequestResource):
    @authenticate()
    @paginate
    def get(self, session, user=None, page=None, per_page=None):
        allele_filters = [allele.Allele.id.in_(queries.workflow_alleles_finalized(session))]
        if user is not None:
            allele_filters.append(
                allele.Allele.id.in_(
                    queries.workflow_alleles_for_genepanels(session, user.group.genepanels)
                )
            )

        alleleinterpretation_allele_ids, count = get_alleles_existing_alleleinterpretation(
            session, and_(*allele_filters), page=page, per_page=per_page
        )
        alleleinterpretation_allele_ids = [a[0] for a in alleleinterpretation_allele_ids]

        gp_allele_ids = get_alleleinterpretation_gp_allele_ids(
            session, alleleinterpretation_allele_ids
        )

        result = load_genepanel_alleles(session, gp_allele_ids)

        # Re-sort result, since the db queries in load_genepanel_alleles doesn't handle sorting
        result.sort(key=lambda x: alleleinterpretation_allele_ids.index(x["allele"]["id"]))
        return result, count


class OverviewAnalysisFinalizedResource(LogRequestResource):
    @authenticate()
    @paginate
    def get(self, session, user=None, page=None, per_page=None):
        return get_finalized_analyses(session, user=user, page=page, per_page=per_page)


class OverviewAnalysisResource(LogRequestResource):
    @authenticate()
    def get(self, session, user=None):
        return get_categorized_analyses(session, user=user)


class OverviewAnalysisByClassifiedResource(LogRequestResource):
    @authenticate()
    def get(self, session, user=None):

        # Filter out alleles
        filterconfigs = queries.get_valid_filter_configs(session, user.group_id)

        if filterconfigs.count() != 1:
            raise ApiError(
                "Unable to find single filter config appropriate for overview filtering. Found {} filterconfigs.".format(
                    filterconfigs.count()
                )
            )

        filterconfig_id = filterconfigs.one().id

        categorized_analyses = get_categorized_analyses(session, user=user)
        not_started_analyses = categorized_analyses.pop("not_started")
        not_started_categories = categorize_analyses_by_findings(
            session, not_started_analyses, filterconfig_id
        )

        categorized_analyses.update(
            {
                "not_started_missing_alleleassessments": not_started_categories[
                    "missing_alleleassessments"
                ],
                "not_started_all_classified": not_started_categories["with_findings"]
                + not_started_categories["without_findings"],
            }
        )
        marked_review_analyses = categorized_analyses.pop("marked_review")
        marked_review_categories = categorize_analyses_by_findings(
            session, marked_review_analyses, filterconfig_id
        )
        categorized_analyses.update(
            {
                "marked_review_missing_alleleassessments": marked_review_categories[
                    "missing_alleleassessments"
                ],
                "marked_review_all_classified": marked_review_categories["with_findings"]
                + marked_review_categories["without_findings"],
            }
        )
        return categorized_analyses


class OverviewUserStatsResource(LogRequestResource):
    @authenticate()
    def get(self, session, user=None):

        stats = dict()

        stats["analyses_cnt"] = (
            session.query(sample.Analysis)
            .join(workflow.AnalysisInterpretation)
            .filter(workflow.AnalysisInterpretation.user_id == user.id)
            .distinct()
            .count()
        )

        stats["alleles_cnt"] = (
            session.query(allele.Allele)
            .join(workflow.AlleleInterpretation)
            .filter(workflow.AlleleInterpretation.user_id == user.id)
            .distinct()
            .count()
        )

        return stats
