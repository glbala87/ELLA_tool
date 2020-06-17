from typing import Dict, Any, DefaultDict, Tuple, Set
from collections import defaultdict
from sqlalchemy import func, tuple_, and_
from sqlalchemy.orm import defer, joinedload
from vardb.datamodel import sample, workflow, allele, genotype, gene

from datalayer import AlleleDataLoader, queries
from datalayer.workflowcategorization import (
    get_categorized_analyses,
    get_categorized_alleles,
    get_finalized_analysis_ids,
)
from api import schemas
from api.v1.resource import LogRequestResource
from api.util.util import authenticate, paginate


def load_alleles(session, allele_id_genepanel):
    """
    Loads in allele data from AlleleDataLoader for all allele ids given by input structure:

    allele_id_genepanel = [
        (1, ('HBOC', 'v01')),
        ...
    ]

    Returns [
        {
            'genepanel': {...genepanel data...},
            'allele': {...allele data...},
            'date_created': '<dateisoformat>',
            'priority': <int>,
            'review_comment': <str>,
            'interpretations': [{...interpretation_data...}, ...],
        },
        ...
    ]
    """

    # Preload all alleles
    all_allele_ids = [a[0] for a in allele_id_genepanel]
    alleles_by_id = dict(
        session.query(allele.Allele.id, allele.Allele)
        .filter(allele.Allele.id.in_(all_allele_ids))
        .all()
    )

    # Preload interpretations for each allele
    interpretations = (
        session.query(workflow.AlleleInterpretation)
        .options(defer("state"), defer("user_state"))
        .filter(workflow.AlleleInterpretation.allele_id.in_(all_allele_ids))
        .order_by(workflow.AlleleInterpretation.date_last_update)
        .all()
    )

    # Preload genepanels
    gp_keys = set([a[1] for a in allele_id_genepanel])
    genepanels = (
        session.query(gene.Genepanel)
        .filter(tuple_(gene.Genepanel.name, gene.Genepanel.version).in_(gp_keys))
        .all()
    )

    # Load highest priority for each allele.
    priority_by_allele_id = dict(queries.workflow_allele_priority(session).all())

    # Load review comments
    review_comment_by_allele_id = dict(queries.workflow_allele_review_comment(session).all())

    # Set structures/loaders
    final_alleles = list()
    adl = AlleleDataLoader(session)
    alleleinterpretation_schema = schemas.AlleleInterpretationOverviewSchema()

    # Create output data
    # Bundle allele_ids with genepanel to increase performance
    gp_allele_ids: DefaultDict[Tuple[str, str], Set[int]] = defaultdict(set)
    for allele_id, gp_key in allele_id_genepanel:
        gp_allele_ids[gp_key].add(allele_id)

    for gp_key, allele_ids in sorted(gp_allele_ids.items(), key=lambda x: x[0]):
        genepanel = next(g for g in genepanels if g.name == gp_key[0] and g.version == gp_key[1])
        gp_alleles = [alleles_by_id[a_id] for a_id in allele_ids]

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
            allele_interpretations = [i for i in interpretations if i.allele_id == a["id"]]
            dumped_interpretations = [
                alleleinterpretation_schema.dump(i).data for i in allele_interpretations
            ]

            final_alleles.append(
                {
                    "genepanel": {"name": genepanel.name, "version": genepanel.version},
                    "allele": a,
                    "date_created": min(
                        [i.date_created for i in allele_interpretations]
                    ).isoformat(),
                    "priority": priority_by_allele_id.get(a["id"], 1),
                    "review_comment": review_comment_by_allele_id.get(a["id"], None),
                    "interpretations": dumped_interpretations,
                }
            )

    return final_alleles


def load_analyses(session, analysis_ids, user):
    """
    Loads in analysis data for all analysis ids given in input.
    Analyses are further restricted to the access for the provided user.


    Returns [
        {
            <AnalysisSchema> +
            "review_comment": <str>,
            "priority": <int>,
            "warning_cleared": <bool>
        },
        ...
    ]
    """
    aschema = schemas.AnalysisSchema()

    user_analysis_ids = queries.analysis_ids_for_user(session, user)

    analyses = (
        session.query(sample.Analysis)
        .options(joinedload(sample.Analysis.interpretations).defer("state").defer("user_state"))
        .filter(sample.Analysis.id.in_(user_analysis_ids), sample.Analysis.id.in_(analysis_ids))
        .order_by(
            func.coalesce(sample.Analysis.date_requested, sample.Analysis.date_deposited).desc()
        )
        .all()
    )
    # FIXME: many=True is broken when some fields (date_requested) are None
    loaded_analyses = [aschema.dump(a).data for a in analyses]

    # Load in priority, warning_cleared and review_comment
    analysis_ids = [a.id for a in analyses]
    priorities = queries.workflow_analyses_priority(session, analysis_ids).all()
    review_comments = queries.workflow_analyses_review_comment(session, analysis_ids).all()
    warnings_cleared = queries.workflow_analyses_warning_cleared(session, analysis_ids).all()

    for analysis in loaded_analyses:
        priority = next((p.priority for p in priorities if p.analysis_id == analysis["id"]), 1)
        analysis["priority"] = priority
        review_comment = next(
            (rc.review_comment for rc in review_comments if rc.analysis_id == analysis["id"]), None
        )
        if review_comment:
            analysis["review_comment"] = review_comment
        warning_cleared = next(
            (wc.warning_cleared for wc in warnings_cleared if wc.analysis_id == analysis["id"]),
            None,
        )
        if warning_cleared:
            analysis["warning_cleared"] = warning_cleared

    return loaded_analyses


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

    analysis_gp_allele_ids: DefaultDict[Tuple[str, str], Set[int]] = defaultdict(set)

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


def get_alleleinterpretation_allele_ids_genepanel(session, allele_ids):
    """
    Creates a list of allele ids with genepanel as matched provided allele_ids.

    Only select the latest interpretation for each allele_id to avoid fetching multiple genepanels
    as they can differ between the interpretations.

    :param session: database session
    :param alleleinterpretation_allele_ids: List of allele ids connected to AlleleInterpretations

    Returns a list of format:
        [
            (1, ('HBOC', 'v01')),
            (2, ('SomethingElse', 'v01')),
        ]
    """

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
            workflow.AlleleInterpretation.allele_id.in_(allele_ids),
            workflow.AlleleInterpretation.id == latest_interpretation.c.id,
        )
        .distinct()
    )

    return [(a[2], (a[0], a[1])) for a in allele_ids_genepanels]


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
    @authenticate()
    def get(self, session, user=None):
        categorized_allele_ids = get_categorized_alleles(session, user=user)

        result: Dict[str, Any] = dict()
        for key, allele_ids in categorized_allele_ids.items():
            allele_id_genepanel = get_alleleinterpretation_allele_ids_genepanel(session, allele_ids)
            result[key] = load_alleles(session, allele_id_genepanel)

        return result


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

        allele_ids_genepanel = get_alleleinterpretation_allele_ids_genepanel(
            session, alleleinterpretation_allele_ids
        )

        result = load_alleles(session, allele_ids_genepanel)

        # Re-sort result, since the db queries in load_alleles doesn't handle sorting
        result.sort(key=lambda x: alleleinterpretation_allele_ids.index(x["allele"]["id"]))
        return result, count


class OverviewAnalysisFinalizedResource(LogRequestResource):
    @authenticate()
    @paginate
    def get(self, session, user=None, page=None, per_page=None):
        finalized_analysis_ids, count = get_finalized_analysis_ids(
            session, user=user, page=page, per_page=per_page
        )
        loaded_analyses = load_analyses(session, finalized_analysis_ids, user)

        return loaded_analyses, count


class OverviewAnalysisResource(LogRequestResource):
    @authenticate()
    def get(self, session, user=None):
        categorized_analysis_ids = get_categorized_analyses(session, user=user)

        result = {}
        for key, analysis_ids in categorized_analysis_ids.items():
            result[key] = load_analyses(session, analysis_ids, user)

        return result


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
