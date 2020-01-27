import itertools
from collections import defaultdict
from sqlalchemy import func, or_, and_
from sqlalchemy.orm import aliased, joinedload
from vardb.datamodel import sample, workflow, assessment, allele, genotype
from datalayer import AlleleFilter, queries
from api import schemas, ApiError
from api.config import config


def _categorize_allele_ids_findings(session, allele_ids):
    """
    Categorizes alleles based on their classification findings.
    A finding is defined from the 'include_analysis_with_findings' flag in config.

    The allele ids are divided into three categories:

    - with_findings:
        alleles that have valid alleleassessments and classification is in findings.

    - without_findings:
        alleles that have valid alleleassessments, but classification is not in findings.

    - missing_alleleassessments:
        alleles that are missing alleleassessments or the alleleassessment is outdated.

    :returns: A dict() of set()
    """
    classification_options = config["classification"]["options"]
    classification_findings = [
        o["value"] for o in classification_options if o.get("include_analysis_with_findings")
    ]
    classification_wo_findings = [
        o["value"] for o in classification_options if not o.get("include_analysis_with_findings")
    ]

    categorized_allele_ids = {
        "with_findings": session.query(assessment.AlleleAssessment.allele_id)
        .filter(
            assessment.AlleleAssessment.allele_id.in_(allele_ids),
            assessment.AlleleAssessment.classification.in_(classification_findings),
            *queries.valid_alleleassessments_filter(session)
        )
        .all(),
        "without_findings": session.query(assessment.AlleleAssessment.allele_id)
        .filter(
            assessment.AlleleAssessment.allele_id.in_(allele_ids),
            assessment.AlleleAssessment.classification.in_(classification_wo_findings),
            *queries.valid_alleleassessments_filter(session)
        )
        .all(),
        "missing_alleleassessments": session.query(allele.Allele.id)
        .outerjoin(assessment.AlleleAssessment)
        .filter(
            allele.Allele.id.in_(allele_ids),
            or_(
                # outerjoin() gives null values when missing alleleassessment
                assessment.AlleleAssessment.allele_id.is_(None),
                # Include cases where classification isn't valid anymore (notice inversion operator)
                ~and_(*queries.valid_alleleassessments_filter(session)),
            ),
            # The filter below is part of the queries.valid_alleleassessments_filter above.
            # Since we negate that query, we end up including all alleleassessment that are superceeded.
            # We therefore need to explicitly exclude those here.
            assessment.AlleleAssessment.date_superceeded.is_(None),
        )
        .all(),
    }

    # Strip out the tuples from db results and convert to set()
    categorized_allele_ids = {k: set([a[0] for a in v]) for k, v in categorized_allele_ids.items()}
    return categorized_allele_ids


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


def categorize_analyses_by_findings(session, not_started_analyses, filter_config_id):

    # Get all (analysis_id, allele_id) combinations for input analyses.
    # We want to categorize these analyses into with_findings, without_findings and missing_alleleassessments
    # based on the state of their alleles' alleleassessments

    analysis_ids = [a["id"] for a in not_started_analyses]

    analysis_ids_allele_ids = (
        session.query(sample.Analysis.id, allele.Allele.id)
        .join(genotype.Genotype.alleles, sample.Sample, sample.Analysis)
        .filter(sample.Analysis.id.in_(analysis_ids))
        .all()
    )

    # Now we have all the alleles, so what remains is to see which alleles are
    # filtered out, which have findings, which are normal and which are without alleleassessments
    # For performance, we first categorize the allele ids in isolation,
    # then connect them to the analyses afterwards
    all_allele_ids = [a[1] for a in analysis_ids_allele_ids]

    # Get a list of candidate genepanels per allele id
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
            allele.Allele.id.in_(all_allele_ids),
        )
        .distinct()
        .all()
    )

    # Make a dict of (gp_name, gp_version): [allele_ids] for use with AlleleFilter
    gp_allele_ids = defaultdict(list)
    for entry in allele_ids_genepanels:
        gp_allele_ids[(entry[0], entry[1])].append(entry[2])

    af = AlleleFilter(session)
    gp_nonfiltered_allele_ids = af.filter_alleles(filter_config_id, gp_allele_ids)
    nonfiltered_allele_ids = set(
        itertools.chain.from_iterable(
            [v["allele_ids"] for v in list(gp_nonfiltered_allele_ids.values())]
        )
    )

    # Now we can start to check our analyses and categorize them
    # First, sort into {analysis_id: [allele_ids]}
    analysis_ids_allele_ids_map = defaultdict(set)
    for a in analysis_ids_allele_ids:
        analysis_ids_allele_ids_map[a[0]].add(a[1])

    categories = {"with_findings": [], "without_findings": [], "missing_alleleassessments": []}

    # Next, compare the allele ids for each analysis and see which category they end up in
    # with regards to the categorized_allele_ids we created earlier.
    # Working with sets only for simplicity (& is intersection, < is subset)
    categorized_allele_ids = _categorize_allele_ids_findings(session, nonfiltered_allele_ids)
    for analysis_id, analysis_allele_ids in analysis_ids_allele_ids_map.items():
        analysis_nonfiltered_allele_ids = analysis_allele_ids & nonfiltered_allele_ids
        analysis_filtered_allele_ids = analysis_allele_ids - analysis_nonfiltered_allele_ids
        analysis = next(a for a in not_started_analyses if a["id"] == analysis_id)

        # One or more allele is missing alleleassessment
        if analysis_nonfiltered_allele_ids & categorized_allele_ids["missing_alleleassessments"]:
            categories["missing_alleleassessments"].append(analysis)
        # One or more allele has a finding
        elif analysis_nonfiltered_allele_ids & categorized_allele_ids["with_findings"]:
            categories["with_findings"].append(analysis)
        # All alleles are without findings
        # Special case: All alleles were filtered out. Treat as without_findings.
        elif (
            analysis_nonfiltered_allele_ids
            and analysis_nonfiltered_allele_ids <= categorized_allele_ids["without_findings"]
        ) or analysis_allele_ids == analysis_filtered_allele_ids:
            categories["without_findings"].append(analysis)
        # All possible cases should have been taken care of above
        else:
            raise ApiError("Allele was not categorized correctly. This may indicate a bug.")

    return categories
