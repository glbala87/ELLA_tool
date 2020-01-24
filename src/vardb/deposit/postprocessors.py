import datetime
import pytz
from datalayer import SnapshotCreator
from api.v1.resources.workflow import helpers
from api.v1.resources.overview import categorize_analyses_by_findings
from api import schemas
from vardb.datamodel import workflow, annotation, assessment


def analysis_not_ready_findings(session, analysis, interpretation, filter_config_id):
    """
    Set analysis as 'Not ready' if it has warnings _or_
    there are variants that needs work (verification etc)
    """
    aschema = schemas.AnalysisSchema()
    dumped_analysis = aschema.dump(analysis).data
    without_findings = bool(
        categorize_analyses_by_findings(session, [dumped_analysis], filter_config_id)[
            "without_findings"
        ]
    )

    if analysis.warnings or not without_findings:
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

        allele_annotation_ids = (
            session.query(annotation.Annotation.allele_id, annotation.Annotation.id)
            .filter(
                annotation.Annotation.date_superceeded.is_(None),
                annotation.Annotation.allele_id.in_(allele_ids),
            )
            .all()
        )

        alleleassessments = (
            session.query(assessment.AlleleAssessment)
            .filter(
                assessment.AlleleAssessment.date_superceeded.is_(None),
                assessment.AlleleAssessment.allele_id.in_(allele_ids),
            )
            .all()
        )

        allelereports = (
            session.query(assessment.AlleleReport)
            .filter(
                assessment.AlleleReport.date_superceeded.is_(None),
                assessment.AlleleReport.allele_id.in_(allele_ids),
            )
            .all()
        )

        annotation_data = [
            {"allele_id": a.allele_id, "annotation_id": a.id} for a in allele_annotation_ids
        ]

        SnapshotCreator(session).insert_from_data(
            "analysis",
            interpretation,
            annotation_data,
            alleleassessments,
            allelereports,
            allele_ids=allele_ids,
            excluded_allele_ids=excluded_allele_ids,
        )

        # Finalize interpretation
        interpretation.status = "Done"
        interpretation.finalized = True
        interpretation.user_id = 1
        interpretation.date_last_update = datetime.datetime.now(pytz.utc)
