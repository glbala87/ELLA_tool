import datetime
from vardb.datamodel import allele, assessment, annotation

from api.schemas import AlleleSchema, GenotypeSchema, AnnotationSchema, CustomAnnotationSchema, AlleleAssessmentSchema, ReferenceAssessmentSchema, GenepanelSchema


class AssessmentCreator(object):

    def __init__(self, session):
        self.session = session

    def curate_and_replace(self, alleleassessments=None, referenceassessments=None):
        """
        Curates input assessments and marks previous ones as
        superceeded. The newly curated assessment is linked to the previous one.
        The input assessment(s) are curated regardless whether their status is
        currently 0 (non-curated).

        The method accepts both types, because if you're curating both
        it's important to first curate the ReferenceAssessments in order
        to properly connect them to AlleleAssessments. All current and curated
        ReferenceAssessments are connected to the AlleleAssessments,
        not necessarily just the ones passed as arguments.

        :param alleleassessments: AlleleAssessments to curate (model objects)
        :param alleleassessments: ReferenceAssessments to curate (model objects)
        """
        if referenceassessments:
            self._curate_referenceassessments(referenceassessments)

        if alleleassessments:
            self._curate_alleleassessments(alleleassessments)

            # Attach ReferenceAssessments to the AlleleAssessments at point of curation
            self._attach_referenceassessments(alleleassessments)

    def _attach_referenceassessments(self, alleleassessments):
        """
        For each AlleleAssessment, get all ReferenceAssessments matching
        the allele id and attaches them to the AlleleAssessment table.
        """
        relevant_ra = self.session.query(assessment.ReferenceAssessment).filter(
            assessment.ReferenceAssessment.allele_id.in_([a.allele_id for a in alleleassessments]),
            assessment.ReferenceAssessment.dateSuperceeded == None,
            assessment.ReferenceAssessment.status == 1
        )
        for aa in alleleassessments:
            aa.referenceAssessments = [ra for ra in relevant_ra if ra.allele_id == aa.allele_id]

    def _curate_alleleassessments(self, alleleassessments):
        allele_ids = [aa.allele_id for aa in alleleassessments]

        # Get existing ones to replace
        existing_aas = self.session.query(assessment.AlleleAssessment).filter(
            assessment.AlleleAssessment.allele_id.in_(allele_ids),
            assessment.AlleleAssessment.dateSuperceeded == None,
            assessment.AlleleAssessment.status == 1
        ).all()

        for aa in alleleassessments:
            # Normally there should be just one previous,
            # but it is safer to check as if there were many
            for existing_aa in existing_aas:
                if existing_aa.allele_id == aa.allele_id:
                    existing_aa.dateSuperceeded = datetime.datetime.now()
                    aa.previousAssessment_id = existing_aa.id

            aa.status = 1  # Curate it (regardless of existing status)
            aa.dateLastUpdate = datetime.datetime.now()
            self.session.add(aa)

    def _curate_referenceassessments(self, referenceassessments):
        allele_ids = [ra.allele_id for ra in referenceassessments]
        reference_ids = [ra.reference_id for ra in referenceassessments]

        # Get existing ones to replace
        existing_ras = self.session.query(assessment.ReferenceAssessment).filter(
            assessment.ReferenceAssessment.allele_id.in_(allele_ids),
            assessment.ReferenceAssessment.reference_id.in_(reference_ids),
            assessment.ReferenceAssessment.dateSuperceeded == None,
            assessment.ReferenceAssessment.status == 1
        ).all()

        for ra in referenceassessments:
            # Normally there should be just one previous,
            # but it is safer to check as if there were many
            for existing_ra in existing_ras:
                if existing_ra.allele_id == ra.allele_id and existing_ra.reference_id == ra.reference_id:
                    existing_ra.dateSuperceeded = datetime.datetime.now()
                    ra.previousAssessment_id = existing_ra.id

            ra.status = 1  # Curate it (regardless of existing status)

            self.session.add(ra)
