import logging
from dataclasses import dataclass
import datetime
import pytz
from typing import Dict, Optional, Tuple
from vardb.datamodel import assessment

from api.schemas import AlleleReportSchema
from api import ApiError

log = logging.getLogger(__name__)


@dataclass
class AlleleReportCreatorResult:
    created_allelereport: Optional[assessment.AlleleReport]
    reused_allelereport: Optional[assessment.AlleleReport]

    @property
    def allelereport(self) -> Optional[assessment.AlleleReport]:
        return self.created_allelereport or self.reused_allelereport


class AlleleReportCreator(object):
    def __init__(self, session):
        self.session = session

    def create_from_data(
        self,
        user_id: int,
        allele_id: int,
        allelereport: dict,
        alleleassessment: assessment.AlleleAssessment = None,
        analysis_id: int = None,
    ) -> AlleleReportCreatorResult:
        """
        If alleleassessment is provided, the allelereport will be connected to
        the alleleassessment. If not, it will be stored with alleleassessment_id empty.
        """

        allelereport_obj, reused = self._create_or_reuse_allelereport(
            user_id,
            allele_id,
            allelereport,
            alleleassessment=alleleassessment,
            analysis_id=analysis_id,
        )

        return AlleleReportCreatorResult(
            allelereport_obj if not reused else None, allelereport_obj if reused else None
        )

    def _create_or_reuse_allelereport(
        self,
        user_id: int,
        allele_id: int,
        allelereport: Dict,
        alleleassessment: assessment.AlleleAssessment = None,
        analysis_id: int = None,
    ) -> Tuple[assessment.AlleleReport, bool]:

        assert allelereport["allele_id"] == allele_id

        existing_report: Optional[assessment.AlleleReport] = (
            self.session.query(assessment.AlleleReport)
            .filter(
                assessment.AlleleReport.allele_id == allele_id,
                assessment.AlleleReport.date_superceeded.is_(
                    None
                ),  # Only allowed to reuse valid allelereport
            )
            .one_or_none()
        )

        result_reused: bool = False

        # If existing, check that user saw the current previous version
        if existing_report:
            presented_id = allelereport["presented_allelereport_id"]
            if presented_id != existing_report.id:
                raise ApiError(
                    f"'presented_allelereport_id': {presented_id} does not match latest existing allelereport id: {existing_report.id}"
                )

        if allelereport.get("reuse"):
            assert existing_report
            result_reused = True
            result_allelereport = existing_report
            log.debug("Reused report %s for allele %s", existing_report.id, allele_id)

        else:  # create a new report
            result_reused = False
            assert "id" not in allelereport
            report_object_to_create: assessment.AlleleReport = AlleleReportSchema(strict=True).load(
                allelereport
            ).data
            report_object_to_create.user_id = user_id

            if analysis_id:
                report_object_to_create.analysis_id == analysis_id

            # Check if there's an existing allelereport for this allele. If so, we want to supercede it
            if existing_report:
                existing_report.date_superceeded = datetime.datetime.now(pytz.utc)
                report_object_to_create.previous_report_id = existing_report.id

            result_allelereport = report_object_to_create

            if alleleassessment:
                result_allelereport.alleleassessment_id = alleleassessment.id

            log.info(
                "Created report for allele: %s, it supercedes: %s",
                report_object_to_create.allele_id,
                report_object_to_create.previous_report_id,
            )

        return result_allelereport, result_reused
