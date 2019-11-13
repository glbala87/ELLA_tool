import logging
import datetime
import pytz
from typing import List, Dict
from vardb.datamodel import assessment

from api.schemas import AlleleReportSchema
from api import ApiError


logging.basicConfig(level=logging.DEBUG)
log = logging.getLogger(__name__)


class AlleleReportCreator(object):
    def __init__(self, session):
        self.session = session

    def create_from_data(
        self,
        user_id: int,
        allele_id: int,
        allelereport: dict,
        alleleassessment: assessment.AlleleAssessment = None,
    ):
        """
        If alleleassessment is provided, the allelereport will be connected to
        the alleleassessment. If not, it will be stored with alleleassessment_id empty.
        """

        allelereport_obj, allelereport_reused = self._create_or_reuse_allelereport(
            user_id, allele_id, allelereport, alleleassessment=alleleassessment
        )

        return allelereport_obj, allelereport_reused

    def find_report_presented(self, report, existing_reports, error_if_not_found=True):
        """
        Find a report in list 'existing_reports' whose id == report['presented_allelereport_id']
        """
        match = next(
            (
                e
                for e in existing_reports
                if report["allele_id"] == e.allele_id
                and "presented_allelereport_id" in report
                and report["presented_allelereport_id"] == e.id
            ),
            None,
        )
        if not match and error_if_not_found:
            raise ApiError(
                "Found no matching allele report for allele_id: {}, id: {}. Either the report is outdated or it doesn't exist.".format(
                    report["allele_id"], report["presented_allelereport_id"]
                )
            )

        return match

    def _create_or_reuse_allelereport(
        self,
        user_id: int,
        allele_id: int,
        allelereport: Dict,
        alleleassessment: assessment.AlleleAssessment = None,
    ):

        assert allelereport["allele_id"] == allele_id

        existing_report = (
            self.session.query(assessment.AlleleReport)
            .filter(
                assessment.AlleleReport.allele_id == allele_id,
                assessment.AlleleReport.date_superceeded.is_(
                    None
                ),  # Only allowed to reuse valid allelereport
            )
            .one_or_none()
        )

        result_allelereport: assessment.AlleleReport = None
        result_reused: bool = False

        if allelereport.get("reuse"):
            result_reused = True
            assert allelereport["presented_allelereport_id"] == existing_report.id
            result_allelereport = existing_report
            log.debug("Reused report %s for allele %s", existing_report.id, allele_id)
        else:  # create a new report
            result_reused = False
            assert "id" not in allelereport
            report_object_to_create = AlleleReportSchema(strict=True).load(allelereport).data
            report_object_to_create.user_id = user_id

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
