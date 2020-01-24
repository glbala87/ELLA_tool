import datetime
import pytz
from datalayer import SnapshotCreator
from api import schemas
from api.v1.resources.workflow import helpers
from datalayer import AlleleDataLoader
from datalayer.workflowcategorization import categorize_analyses_by_findings
from vardb.datamodel import workflow, annotation, assessment, allele


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


def analysis_finalize_without_findings(session, analysis, interpretation, filter_config_id):
    """
    Finalizes analyses that are without findings at import time.

    Interpretation is set to system user (id 1) and an entry
    is inserted into the log to indicate reason for finalization.
    """
    aschema = schemas.AnalysisSchema()
    dumped_analysis = aschema.dump(analysis).data
    without_findings = bool(
        categorize_analyses_by_findings(session, [dumped_analysis], filter_config_id)[
            "without_findings"
        ]
    )

    if without_findings and not analysis.warnings:

        # Interpretation is flushed already, so we have an id
        # Log item must be created before finalization so that the dates are correct
        il = workflow.InterpretationLog(
            analysisinterpretation_id=interpretation.id,
            message="Analysis had no findings at time of import. Automatically finalized by system.",
        )
        session.add(il)

        allele_ids, excluded_allele_ids = helpers.get_filtered_alleles(
            session, interpretation, filter_config_id
        )

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
