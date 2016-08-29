import datetime
from vardb.datamodel import allele, assessment, sample

from api.schemas import AlleleReportSchema
from api import ApiError


class AlleleReportCreator(object):

    def __init__(self, session):
        self.session = session

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
        result = self._create_or_reuse_allelereports(allelereports)

        if alleleassessments:
            self._attach_alleleassessments(result[0], alleleassessments)

        return {
            'created': result[0],
            'reused': result[1]
        }

    def _attach_alleleassessments(self, allelereports, alleleassessments):
        """
        For each AlleleReport, get the matching alleleassessment by
        the allele id and attach it to the AlleleReport object.

        :param allelereports: AlleleReport model objects
        :param alleleassessments: AlleleAssessment model objects
        """
        for ar in allelereports:
            ar.alleleassessment = next((a for a in alleleassessments if a.allele_id == ar.allele_id))

    def _create_or_reuse_allelereports(self, allelereports):
        allele_ids = [a['allele_id'] for a in allelereports]

        existing = self.session.query(assessment.AlleleReport).filter(
            assessment.AlleleReport.allele_id.in_(allele_ids),
            assessment.AlleleReport.date_superceeded == None  # Only allowed to reuse valid allelereport
        ).all()

        reused = list()
        created = list()
        # When an 'id' is provided, we check and reuse that allelereport instead of creating it
        for ar in allelereports:
            if 'id' in ar:
                to_reuse = next((e for e in existing if ar['allele_id'] == e.allele_id and ar['id'] == e.id), None)
                if not to_reuse:
                    raise ApiError("Found no matching allelereport for allele_id: {}, id: {}. Either the report is outdated or it doesn't exist.".format(ar['allele_id'], ar['id']))
                reused.append(to_reuse)
            else:
                report_obj = AlleleReportSchema(strict=True).load(ar).data
                report_obj.date_last_update = datetime.datetime.now()

                # Check if there's an existing allelereport for this allele. If so, we want to supercede it
                to_supercede = next((e for e in existing if e.allele_id == ar['allele_id']), None)
                if to_supercede:
                    to_supercede.date_superceeded = datetime.datetime.now()
                    report_obj.previous_report_id = to_supercede.id
                created.append(report_obj)
                self.session.add(report_obj)

        return created, reused
