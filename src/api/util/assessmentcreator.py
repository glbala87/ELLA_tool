import datetime
from vardb.datamodel import allele, assessment, annotation, sample, gene

from api.schemas import AlleleSchema, GenotypeSchema, AnnotationSchema, CustomAnnotationSchema, AlleleAssessmentSchema, ReferenceAssessmentSchema, GenepanelSchema
from api import ApiError


class AssessmentCreator(object):

    def __init__(self, session):
        self.session = session

    def create_from_data(self, alleleassessments=None, referenceassessments=None):
        """
        Takes in lists of data and creates new assessments in database.
        ReferenceAssessments having same allele as the AlleleAssessments,
        are connected to the corresponding AlleleAssessment.

        The method accepts both types, because if you're creating both
        it's important to first create the ReferenceAssessments in order
        to properly connect them to AlleleAssessments.

        You can chose whether to include referenceassessments as part of
        alleleassessment['referenceassessments'] or by supplying them
        through the refereassessment keyword. They will be connected correctly
        through alleleassessments regardless.

        :param alleleassessments: AlleleAssessments to create or reuse (dict data)
        :param referenceassessments: ReferenceAssessments to create or reuse (dict data)
        """

        if referenceassessments is None:
            referenceassessments = list()

        if alleleassessments is None:
            alleleassessments = list()

        aa_created, aa_reused = self._create_or_reuse_alleleassessments(alleleassessments)

        # Check for any referenceassessments included as part of alleleassessments
        for aa in alleleassessments:
            if 'referenceassessments' in aa:
                for f in ['allele_id']:
                    if not all([r[f] == aa[f] for r in aa['referenceassessments']]):
                        raise ApiError("One of the included referenceassessments has a mismatch on {}.".format(f))
                referenceassessments += aa['referenceassessments']

        ra_created, ra_reused = self._create_or_reuse_referenceassessments(referenceassessments)

        # Attach ReferenceAssessments to the AlleleAssessments
        ref_total = ra_created + ra_reused
        if ref_total and aa_created:
            self._attach_referenceassessments(ref_total, aa_created)

        result = dict()
        result.update({
            'referenceassessments': {
                'reused': ra_reused,
                'created': ra_created
            }
        })
        result.update({
            'alleleassessments': {
                'reused': aa_reused,
                'created': aa_created
            }
        })

        return result

    def _attach_referenceassessments(self, referenceassessments, alleleassessments):
        """
        For each AlleleAssessment, get all ReferenceAssessments matching
        the allele id and attaches them to the AlleleAssessment object.

        :param referenceassessments: Refereceassessment model objects
        :param alleleassessments: AlleleAssessment model objects
        """
        for aa in alleleassessments:
            aa.referenceassessments = [ra for ra in referenceassessments if ra.allele_id == aa.allele_id]

    def _create_or_reuse_alleleassessments(self, alleleassessments):
        allele_ids = [a['allele_id'] for a in alleleassessments]
        analysis_id = [a['analysis_id'] for a in alleleassessments if 'analysis_id' in a]

        cache = {
            'annotation': self.session.query(annotation.Annotation).filter(
                annotation.Annotation.allele_id.in_(allele_ids)
            ).all()
        }
        if analysis_id:
            cache['analysis'] = self.session.query(sample.Analysis).filter(
                sample.Analysis.id.in_(analysis_id)
            ).all()

        existing = self.session.query(assessment.AlleleAssessment).filter(
            assessment.AlleleAssessment.allele_id.in_(allele_ids),
            assessment.AlleleAssessment.date_superceeded == None  # Only allowed to reuse valid assessment
        ).all()

        reused = list()
        created = list()
        # When an 'id' is provided, we check and reuse that assessment instead of creating it
        for aa in alleleassessments:
            if 'id' in aa:
                to_reuse = next((e for e in existing if aa['allele_id'] == e.allele_id and aa['id'] == e.id), None)
                if not to_reuse:
                    raise ApiError("Found no matching alleleassessment for allele_id: {}, id: {}. Either the assessment is outdated or it doesn't exist.".format(aa['allele_id'], aa['id']))
                reused.append(to_reuse)
            else:
                assessment_obj = AlleleAssessmentSchema(strict=True).load(aa).data
                assessment_obj.referenceassessments = []  # ReferenceAssessments must be handled separately, and not included as part of data
                assessment_obj.date_last_update = datetime.datetime.now()

                # Link assessment to current valid annotation (through the allele id)
                valid_annotation = next((an for an in cache['annotation'] if an.allele_id == aa['allele_id']), None)
                if not allele:
                    raise ApiError("Couldn't find annotation for provided allele_id: {}.".format(aa['allele_id']))
                assessment_obj.annotation_id = valid_annotation.id

                # If analysis_id provided, link assessment to genepanel through analysis
                if 'analysis_id' in aa:
                    assessment_analysis = next(a for a in cache['analysis'] if a.id == aa['analysis_id'])
                    assessment_obj.genepanel_name = assessment_analysis.genepanel_name
                    assessment_obj.genepanel_version = assessment_analysis.genepanel_version
                elif not ('genepanel_name' in aa and 'genepanel_version' in aa):
                    raise ApiError("No 'analysis_id' and no 'genepanel_name' + 'genepanel_version' given for assessment")

                # Check if there's an existing assessment for this allele. If so, we want to supercede it
                to_supercede = next((e for e in existing if e.allele_id == aa['allele_id']), None)
                if to_supercede:
                    to_supercede.date_superceeded = datetime.datetime.now()
                    assessment_obj.previous_assessment_id = to_supercede.id
                created.append(assessment_obj)
                self.session.add(assessment_obj)

        return created, reused

    def _create_or_reuse_referenceassessments(self, referenceassessments):

        analysis_id = [a['analysis_id'] for a in referenceassessments if 'analysis_id' in a]

        cache = {}
        if analysis_id:
            cache['analysis'] = self.session.query(sample.Analysis).filter(
                sample.Analysis.id.in_(analysis_id)
            ).all()

        allele_ids = [ra['allele_id'] for ra in referenceassessments]
        reference_ids = [ra['reference_id'] for ra in referenceassessments]

        existing = self.session.query(assessment.ReferenceAssessment).filter(
            assessment.ReferenceAssessment.allele_id.in_(allele_ids),
            assessment.ReferenceAssessment.reference_id.in_(reference_ids),
            assessment.ReferenceAssessment.date_superceeded == None  # Only allowed to reuse valid assessment
        ).all()

        reused = list()
        created = list()
        # When an 'id' is provided, we check and reuse that assessment instead of creating it
        for ra in referenceassessments:
            if 'id' in ra:
                to_reuse = next((e for e in existing if ra['allele_id'] == e.allele_id and ra['reference_id'] == e.reference_id and ra['id'] == e.id), None)
                if not to_reuse:
                    raise ApiError("Found no matching referenceassessment for allele_id: {}, reference_id: {}, id: {}. Either the assessment is outdated or it doesn't exist.".format(ra['allele_id'], ra['reference_id'], ra['id']))
                reused.append(to_reuse)
            else:
                assessment_obj = ReferenceAssessmentSchema(strict=True).load(ra).data
                assessment_obj.date_last_update = datetime.datetime.now()

                # Link assessment to genepanel through analysis
                if 'analysis_id' in ra:
                    assessment_analysis = next(a for a in cache['analysis'] if a.id == ra['analysis_id'])
                    assessment_obj.genepanel_name = assessment_analysis.genepanel_name
                    assessment_obj.genepanel_version = assessment_analysis.genepanel_version
                elif not ('genepanel_name' in ra and 'genepanel_version' in ra):
                    raise ApiError("No 'analysis_id' and no 'genepanel_name' + 'genepanel_version' given for refernceassessment")

                # Check if there's an existing assessment for this allele/reference. If so, we want to supercede it
                to_supercede = next((e for e in existing if ra['allele_id'] == e.allele_id and ra['reference_id'] == e.reference_id), None)
                if to_supercede:
                    to_supercede.date_superceeded = datetime.datetime.now()
                    assessment_obj.previous_assessment_id = to_supercede.id
                created.append(assessment_obj)
                self.session.add(assessment_obj)

        return created, reused


