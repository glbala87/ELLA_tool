from sqlalchemy import func
from sqlalchemy.orm import aliased, joinedload
from vardb.datamodel import sample, workflow
from datalayer import queries
from api import schemas


def _get_analysis_ids_for_user(session, user=None):
    analysis_ids_for_user = session.query(sample.Analysis.id)
    # Restrict analyses to analyses matching this user's group's genepanels
    if user is not None:
        analyses_for_genepanels = queries.workflow_analyses_for_genepanels(
            session, user.group.genepanels
        )
        analysis_ids_for_user = analysis_ids_for_user.filter(
            sample.Analysis.id.in_(analyses_for_genepanels)
        )
    return analysis_ids_for_user


def get_categorized_alleles(session, user=None):

    categories = [
        ("not_started", queries.workflow_alleles_interpretation_not_started(session)),
        ("marked_review", queries.workflow_alleles_review_not_started(session)),
        ("ongoing", queries.workflow_alleles_ongoing(session)),
    ]

    categorized_allele_ids = dict()
    for key, subquery in categories:
        filters = [workflow.AlleleInterpretation.allele_id.in_(subquery)]
        if user:
            filters.append(
                workflow.AlleleInterpretation.allele_id.in_(
                    queries.workflow_alleles_for_genepanels(session, user.group.genepanels)
                )
            )
        categorized_allele_ids[key] = (
            session.query(workflow.AlleleInterpretation.allele_id)
            .filter(*filters)
            .distinct()
            .scalar_all()
        )

    return categorized_allele_ids


def get_categorized_analyses(session, user=None):

    user_analysis_ids = _get_analysis_ids_for_user(session, user=user)

    categories = [
        ("not_ready", queries.workflow_analyses_notready_not_started(session)),
        ("not_started", queries.workflow_analyses_interpretation_not_started(session)),
        ("marked_review", queries.workflow_analyses_review_not_started(session)),
        ("marked_medicalreview", queries.workflow_analyses_medicalreview_not_started(session)),
        ("ongoing", queries.workflow_analyses_ongoing(session)),
    ]

    aschema = schemas.AnalysisSchema()
    final_analyses = dict()
    for key, subquery in categories:
        analyses = (
            session.query(sample.Analysis)
            .options(joinedload(sample.Analysis.interpretations).defer("state").defer("user_state"))
            .filter(sample.Analysis.id.in_(user_analysis_ids), sample.Analysis.id.in_(subquery))
            .all()
        )
        # FIXME: many=True is broken when some fields (date_requested) are None
        final_analyses[key] = [aschema.dump(a).data for a in analyses]

        # Load in priority, warning_cleared and review_comment
        analysis_ids = [a.id for a in analyses]
        priorities = queries.workflow_analyses_priority(session, analysis_ids).all()
        review_comments = queries.workflow_analyses_review_comment(session, analysis_ids).all()
        warnings_cleared = queries.workflow_analyses_warning_cleared(session, analysis_ids).all()

        for analysis in final_analyses[key]:
            priority = next((p.priority for p in priorities if p.analysis_id == analysis["id"]), 1)
            analysis["priority"] = priority
            review_comment = next(
                (rc.review_comment for rc in review_comments if rc.analysis_id == analysis["id"]),
                None,
            )
            if review_comment:
                analysis["review_comment"] = review_comment
            warning_cleared = next(
                (wc.warning_cleared for wc in warnings_cleared if wc.analysis_id == analysis["id"]),
                None,
            )
            if warning_cleared:
                analysis["warning_cleared"] = warning_cleared

    return final_analyses


def get_finalized_analyses(session, user=None, page=None, per_page=None):

    user_analysis_ids = _get_analysis_ids_for_user(session, user=user)

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
        session.query(new_analysis)
        .join(sorted_analysis_ids, new_analysis.id == sorted_analysis_ids.c.analysis_id)
        .order_by(sorted_analysis_ids.c.max_date_last_update.desc())
    )

    count = finalized_analyses.count()

    if page and per_page:
        start = (page - 1) * per_page
        end = page * per_page
        finalized_analyses = finalized_analyses.slice(start, end)

    aschema = schemas.AnalysisSchema()
    # FIXME: many=True is broken when some fields (date_requested) are None
    finalized_analyses_data = [aschema.dump(a).data for a in finalized_analyses.all()]

    # Insert review comment in analyses
    analysis_ids = [a["id"] for a in finalized_analyses_data]
    review_comments = dict(queries.workflow_analyses_review_comment(session, analysis_ids))
    for a in finalized_analyses_data:
        if a["id"] in review_comments:
            a["review_comment"] = review_comments[a["id"]]

    return finalized_analyses_data, count
