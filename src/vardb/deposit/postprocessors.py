import datetime
import pytz
from datalayer import SnapshotCreator, queries
from vardb.datamodel import workflow, assessment, allele
from api.v1.resources.workflow import helpers
from datalayer import AlleleDataLoader
from api.config import config


def analysis_not_ready_warnings(session, analysis, interpretation, filter_config_id):
    """
    Set analysis as 'Not ready' if it has warnings _or_
    there are variants that needs verification.
    """
    allele_ids, excluded_allele_ids = helpers.get_filtered_alleles(
        session, interpretation, filter_config_id
    )

    alleles = session.query(allele.Allele).filter(allele.Allele.id.in_(allele_ids)).all()

    loaded_alleles = AlleleDataLoader(session).from_objs(
        alleles, analysis_id=interpretation.analysis_id
    )

    any_needs_verification = False
    for l in loaded_alleles:
        for s in l["samples"]:
            if s["proband"] and s["genotype"]["needs_verification"]:
                any_needs_verification = True

    if analysis.warnings or any_needs_verification:
        interpretation.workflow_status = "Not ready"


def analysis_tag_all_classified(session, analysis, interpretation, filter_config_id):
    """
    Adds an overview comment with a "category" for the analysis.

    Currently adds:

    - 'ALL CLASSIFIED' if the analysis has no variants
    missing classification.

    - 'NO VARIANTS' if the analysis has no variants
    using the given filterconfig (which normally is the default one)
    """

    allele_ids, _ = helpers.get_filtered_alleles(session, interpretation, filter_config_id)

    # Get alleles with missing or outdated alleleassessments
    allele_ids_with_alleleasssessment = (
        session.query(assessment.AlleleAssessment.allele_id)
        .filter(
            assessment.AlleleAssessment.allele_id.in_(allele_ids),
            *queries.valid_alleleassessments_filter(session)
        )
        .all()
    )

    if not allele_ids:
        il = workflow.InterpretationLog(
            analysisinterpretation_id=interpretation.id, review_comment="NO VARIANTS"
        )
        session.add(il)
    elif not set(allele_ids) - set(allele_ids_with_alleleasssessment):
        il = workflow.InterpretationLog(
            analysisinterpretation_id=interpretation.id, review_comment="ALL CLASSIFIED"
        )
        session.add(il)
    else:
        il = workflow.InterpretationLog(
            analysisinterpretation_id=interpretation.id, review_comment="MISSING CLASSIFICATIONS"
        )
        session.add(il)


def analysis_finalize_without_findings(session, analysis, interpretation, filter_config_id):
    """
    Finalizes analyses that are without findings at import time.

    Interpretation is set to system user (id 1) and an entry
    is inserted into the log to indicate reason for finalization.
    """

    allele_ids, excluded_allele_ids = helpers.get_filtered_alleles(
        session, interpretation, filter_config_id
    )

    # Get classifications from config that is defined as a 'finding'
    classification_options = config["classification"]["options"]
    classification_wo_findings = [
        o["value"] for o in classification_options if not o.get("include_analysis_with_findings")
    ]

    # Get alleles with an alleleasssment having any of those 'findings'
    allele_ids_without_findings = (
        session.query(assessment.AlleleAssessment.allele_id)
        .filter(
            assessment.AlleleAssessment.allele_id.in_(allele_ids),
            assessment.AlleleAssessment.classification.in_(classification_wo_findings),
            *queries.valid_alleleassessments_filter(session)
        )
        .all()
    )

    # This implicitly also checks for any missing alleleassessments via allele_ids_without_findings
    without_findings = set(allele_ids) - set(allele_ids_without_findings) == set()

    if without_findings and not analysis.warnings:

        # Interpretation is flushed already, so we have an id
        # Log item must be created before finalization so that the dates are correct
        il = workflow.InterpretationLog(
            analysisinterpretation_id=interpretation.id,
            message="Analysis had no findings at time of import. Automatically finalized by system.",
        )
        session.add(il)

        annotation_ids = (
            session.query(annotation.Annotation.id)
            .filter(
                annotation.Annotation.date_superceeded.is_(None),
                annotation.Annotation.allele_id.in_(allele_ids),
            )
            .scalar_all()
        )

        custom_annotation_ids = (
            session.query(annotation.CustomAnnotation.id)
            .filter(
                annotation.CustomAnnotation.date_superceeded.is_(None),
                annotation.CustomAnnotation.allele_id.in_(allele_ids),
            )
            .scalar_all()
        )

        alleleassessment_ids = (
            session.query(assessment.AlleleAssessment.id)
            .filter(
                assessment.AlleleAssessment.date_superceeded.is_(None),
                assessment.AlleleAssessment.allele_id.in_(allele_ids),
            )
            .scalar_all()
        )

        allelereport_ids = (
            session.query(assessment.AlleleReport.id)
            .filter(
                assessment.AlleleReport.date_superceeded.is_(None),
                assessment.AlleleReport.allele_id.in_(allele_ids),
            )
            .scalar_all()
        )

        SnapshotCreator(session).insert_from_data(
            allele_ids,
            "analysis",
            interpretation,
            annotation_ids,
            custom_annotation_ids,
            alleleassessment_ids,
            allelereport_ids,
            excluded_allele_ids=excluded_allele_ids,
        )

        # Finalize interpretation
        interpretation.status = "Done"
        interpretation.finalized = True
        interpretation.user_id = 1
        interpretation.date_last_update = datetime.datetime.now(pytz.utc)
