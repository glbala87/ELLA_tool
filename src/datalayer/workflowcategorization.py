from typing import Dict, List, Optional

from api.util.types import AlleleCategories, AnalysisCategories
from sqlalchemy import func
from sqlalchemy.orm import Session, aliased
from vardb.datamodel import sample, user, workflow

from datalayer import queries


def get_categorized_alleles(session: Session, user: Optional[user.User] = None):
    """
    Categorizes alleles according to workflow status and returns subqueries
    for their allele_ids per category.
    """
    categories = {
        AlleleCategories.NOT_STARTED: queries.workflow_alleles_interpretation_not_started(session),
        AlleleCategories.MARKED_REVIEW: queries.workflow_alleles_review_not_started(session),
        AlleleCategories.ONGOING: queries.workflow_alleles_ongoing(session),
    }

    categorized_allele_ids: Dict[str, List[workflow.AlleleInterpretation]] = dict()
    for key, subquery in categories.items():
        filters = [workflow.AlleleInterpretation.allele_id.in_(subquery)]
        if user:
            filters.append(
                workflow.AlleleInterpretation.allele_id.in_(
                    queries.workflow_alleles_for_genepanels(session, user.group.genepanels)
                )
            )
        categorized_allele_ids[key] = (
            session.query(workflow.AlleleInterpretation.allele_id).filter(*filters).distinct()
        )

    return categorized_allele_ids


def get_categorized_analyses(session: Session, user: Optional[user.User] = None):
    """
    Categorizes analyses according to workflow status and returns subqueries
    for their analysis_ids per category.
    """
    categories = {
        AnalysisCategories.NOT_READY: queries.workflow_analyses_notready_not_started(session),
        AnalysisCategories.NOT_STARTED: queries.workflow_analyses_interpretation_not_started(
            session
        ),
        AnalysisCategories.MARKED_REVIEW: queries.workflow_analyses_review_not_started(session),
        AnalysisCategories.MARKED_MEDICALREVIEW: queries.workflow_analyses_medicalreview_not_started(
            session
        ),
        AnalysisCategories.ONGOING: queries.workflow_analyses_ongoing(session),
    }
    return categories


def get_finalized_analysis_ids(
    session: Session, user: user.User, page: Optional[int] = None, per_page: Optional[int] = None
):

    user_analysis_ids = queries.analysis_ids_for_user(session, user)

    sorted_analysis_ids = (
        session.query(
            sample.Analysis.id.label("analysis_id"),
            func.max(workflow.AnalysisInterpretation.date_last_update).label(
                "max_date_last_update"
            ),
        )
        .join(workflow.AnalysisInterpretation)
        .filter(
            sample.Analysis.id.in_(queries.workflow_analyses_finalized(session)),
            sample.Analysis.id.in_(user_analysis_ids),
        )
        .group_by(sample.Analysis.id)
        .subquery()
    )

    # We need to give a hint to sqlalchemy to use the query's analysis
    # instead of the subquery's 'sample.Analysis' in the join
    new_analysis = aliased(sample.Analysis)
    finalized_analyses = (
        session.query(new_analysis.id)
        .join(sorted_analysis_ids, new_analysis.id == sorted_analysis_ids.c.analysis_id)
        .order_by(sorted_analysis_ids.c.max_date_last_update.desc())
    )

    count = finalized_analyses.count()

    if page and per_page:
        start = (page - 1) * per_page
        end = page * per_page
        finalized_analyses = finalized_analyses.slice(start, end)

    return (finalized_analyses.distinct(), count)
