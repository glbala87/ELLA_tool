import logging
import datetime
from vardb.datamodel import assessment

from api.schemas import AlleleReportSchema
from api import ApiError


logging.basicConfig(level=logging.DEBUG)
log = logging.getLogger(__name__)


class AlleleReportCreator(object):

    def __init__(self, session):
        self.session = session

    @staticmethod
    def _possible_reuse(item):
        return 'reuse' in item and item['reuse']

    def create_from_data(self, allelereports, alleleassessments=None):
        """
        Takes in lists of data and either reuse or creates new reports in database.

        If alleleassessments are provided, the allelereports will be connected to
        the corresponding alleleassessment (matched by allele). If not, it will be stored
        with alleleassessment_id empty.

        :param allelereports: AlleleReports to create or reuse (list of dict data)
        :param alleleassessments: AlleleAssessments to connect the reports (list of model objects)
        :returns: Dict with keys 'reused' and 'created'
        """

        created_reports, reused_reports = self._create_or_reuse_allelereports(allelereports)

        if alleleassessments:
            for created_report in created_reports:
                created_report.alleleassessment = next((a for a in alleleassessments if a.allele_id == created_report.allele_id))

        return {
            'created': created_reports,
            'reused': reused_reports
        }

    def find_report_presented(self, report, existing_reports, error_if_not_found=True):
        """
        Find a report in list 'existing_reports' whose id == report['presented_allelereport_id']
        """
        match = next((e for e in existing_reports
                      if report['allele_id'] == e.allele_id
                      and 'presented_allelereport_id' in report
                      and report['presented_allelereport_id'] == e.id),
                     None)
        if not match and error_if_not_found:
            raise ApiError(
                "Found no matching allele report for allele_id: {}, id: {}. Either the report is outdated or it doesn't exist.".format(
                    report['allele_id'], report['presented_allelereport_id']))

        return match

    def _create_or_reuse_allelereports(self, allelereports):
        allele_ids = [a['allele_id'] for a in allelereports]

        all_existing_reports = self.session.query(assessment.AlleleReport).filter(
            assessment.AlleleReport.allele_id.in_(allele_ids),
            assessment.AlleleReport.date_superceeded == None  # Only allowed to reuse valid allelereport
        ).all()

        reused = list()
        created = list()
        for report_data in allelereports:
            if AlleleReportCreator._possible_reuse(report_data):
                presented_report = self.find_report_presented(report_data, all_existing_reports)
                reused.append(presented_report)
                log.info("Reused report %s for allele %s", presented_report.id, report_data['allele_id'])
            else:  # create a new report
                if 'id' in report_data:
                    del report_data['id']
                report_object_to_create = AlleleReportSchema(strict=True).load(report_data).data

                now = datetime.datetime.now()
                report_object_to_create.date_last_update = now

                # Check if there's an existing allelereport for this allele. If so, we want to supercede it
                old_report = next((e for e in all_existing_reports if e.allele_id == report_data['allele_id']), None)
                if old_report:
                    old_report.date_superceeded = now
                    report_object_to_create.previous_report_id = old_report.id

                presented_report = self.find_report_presented(report_data, all_existing_reports, error_if_not_found=False)
                created.append(report_object_to_create)
                log.info("Created report for allele: %s, it supercedes: %s", report_object_to_create.allele_id, report_object_to_create.previous_report_id)

        return created, reused
