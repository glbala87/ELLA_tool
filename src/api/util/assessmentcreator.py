import datetime
import pytz
from vardb.datamodel import assessment, sample, attachment


from api.schemas import AlleleAssessmentSchema, ReferenceAssessmentSchema
from api import ApiError

import logging

logging.basicConfig(level=logging.DEBUG)
log = logging.getLogger(__name__)


class AssessmentCreator(object):

    def __init__(self, session):
        self.session = session

    @staticmethod
    def _possible_reuse(item):
        return 'reuse' in item and item['reuse']

    def create_from_data(self, user_id, annotations, alleleassessments, custom_annotations=list(),
                         referenceassessments=list(), attachments=list()):
        """
        Takes in lists of assessment data and (possible) creates new assessments in database.

        Returns all mentioned assessments along with the assessments that was part of the assessment context.

        ReferenceAssessments having same allele as the AlleleAssessments,
        are connected to the corresponding AlleleAssessment.

        The method accepts both types, because if you're creating both
        it's important to first create the ReferenceAssessments in order
        to properly connect them to AlleleAssessments.

        You can chose whether to include referenceassessments as part of
        alleleassessment['referenceassessments'] or by supplying them
        through the refereassessment keyword. They will be connected correctly
        through alleleassessments regardless.

        :param annotations: [{allele_id: 1, annotatation_id: 212}, ...] identifying the annotation for the allele
        :param custom_annotations: [{allele_id: 1, custom_annotatation_id: 212}, ...]  identifying the annotation for the allele
        :param alleleassessments: AlleleAssessments to create or reuse (dict data)
        :param referenceassessments: ReferenceAssessments to create or reuse (dict data)
        :type annotations:

        :return a dict {
            'referenceassessments': {
                'reused': [...]
                'created': [...]
            },
            'alleleassessments': {
                'reused': [...],
                'created': [...]
            }
        }
        with the assessments grouped by allele assessments and reference assessments and
        whether they were created or reused.
        """

        aa_created, aa_reused = self._create_or_reuse_alleleassessments(user_id, annotations, alleleassessments, custom_annotations=custom_annotations)

        included_reference_assessments = self.get_included_referenceassessments(alleleassessments)

        all_reference_assessments = referenceassessments + included_reference_assessments

        ra_created, ra_reused = self._create_or_reuse_referenceassessments(user_id, all_reference_assessments)

        self._attach_referenceassessments(ra_created + ra_reused, aa_created)

        self._attach_attachments(attachments, aa_created)

        return {
            'referenceassessments': {
                'reused': ra_reused,
                'created': ra_created
            },
            'alleleassessments': {
                'reused': aa_reused,
                'created': aa_created
            }
        }

    def get_included_referenceassessments(self, alleleassessments):
        # Get all reference assessments included as part of alleleassessments
        included = list()
        for aa in alleleassessments:
            if 'referenceassessments' in aa:
                for f in ['allele_id']:
                    if not all([ra[f] == aa[f] for ra in aa['referenceassessments']]):
                        raise ApiError(
                            "All included reference assessments must match allele assements on {}.".format(f))
                included += aa['referenceassessments']
        return included

    def _attach_referenceassessments(self, referenceassessments, alleleassessments):
        """
        For each AlleleAssessment, get all ReferenceAssessments matching
        the allele id and attaches them to the AlleleAssessment object.

        :param referenceassessments: Refereceassessment model objects
        :param alleleassessments: AlleleAssessment model objects
        """
        for aa in alleleassessments:
            aa.referenceassessments = [ra for ra in referenceassessments if ra.allele_id == aa.allele_id]

    def _create_or_reuse_alleleassessments(self, user_id, annotations, alleleassessments, custom_annotations=list()):
        """

        :param annotations: [{allele_id: annotation_id}]
        :param alleleassessments:
        :param custom_annotations: [{allele_id: custom_annotation_id}]
        :return: (created, reused)
        """

        def _find_first_matching(seq, predicate):
            if not seq:
                return None
            return next((s for s in seq if predicate(s)), None)

        allele_ids = [a['allele_id'] for a in alleleassessments]
        analysis_ids = [a['analysis_id'] for a in alleleassessments if 'analysis_id' in a]

        cache = {}
        if analysis_ids:
            cache['analysis'] = self.session.query(sample.Analysis).filter(
                sample.Analysis.id.in_(analysis_ids)
            ).all()

        all_existing_assessments = self.session.query(assessment.AlleleAssessment).filter(
            assessment.AlleleAssessment.allele_id.in_(allele_ids),
            assessment.AlleleAssessment.date_superceeded.is_(None)  # Only allowed to reuse valid assessment
        ).all()

        reused_assessments = list()  # list of tuples (presented, None)
        created_assessments = list()  # list of tuples (presented/None, created)
        for assessment_data in alleleassessments:
            if AssessmentCreator._possible_reuse(assessment_data):
                presented_assessment = self.find_assessment_presented(assessment_data, all_existing_assessments)
                reused_assessments.append(presented_assessment)
                log.info("Reused assessment %s for allele %s", presented_assessment.id, assessment_data['allele_id'])
            else:  # create a new assessment
                assessment_obj = AlleleAssessmentSchema(strict=True).load(assessment_data).data
                assessment_obj.user_id = user_id
                assessment_obj.referenceassessments = []  # ReferenceAssessments must be handled separately, and not included as part of data

                # look up the annotations for the allele we assess:
                def annotation_predicate(id_pair):
                    return id_pair['allele_id'] == assessment_data['allele_id']
                annotation_match = _find_first_matching(annotations, annotation_predicate)
                custom_annotation_match = _find_first_matching(custom_annotations, annotation_predicate)

                assessment_obj.annotation_id = annotation_match['annotation_id']
                assessment_obj.custom_annotation_id = custom_annotation_match['custom_annotation_id'] if custom_annotation_match and 'custom_annotation_id' in custom_annotation_match else None

                # If analysis_id provided, link assessment to genepanel through analysis for safety
                # If not analysis_id, genepanel was loaded using schema above.
                if 'analysis_id' in assessment_data:
                    assessment_analysis = next(a for a in cache['analysis'] if a.id == assessment_data['analysis_id'])
                    assessment_obj.genepanel_name = assessment_analysis.genepanel_name
                    assessment_obj.genepanel_version = assessment_analysis.genepanel_version
                elif not ('genepanel_name' in assessment_data and 'genepanel_version' in assessment_data):
                    raise ApiError("No 'analysis_id' and no 'genepanel_name' + 'genepanel_version' given for assessment")

                # Check if there's an existing assessment for this allele. If so, we want to supercede it
                to_supercede = next((e for e in all_existing_assessments if e.allele_id == assessment_data['allele_id']), None)
                if to_supercede:
                    to_supercede.date_superceeded = datetime.datetime.now(pytz.utc)
                    assessment_obj.previous_assessment_id = to_supercede.id

                presented_assessment = self.find_assessment_presented(assessment_data, all_existing_assessments, error_if_not_found=False)
                created_assessments.append(assessment_obj)
                log.info("Created assessment for allele: %s, it supercedes: %s", assessment_obj.allele_id, assessment_obj.previous_assessment_id)

        return created_assessments, reused_assessments

    def find_assessment_presented(self, allele_assessment, existing_assessments, error_if_not_found=True):
        """
        Find an assessment in list 'existing_assessments' whose id == allele_assessment['presented_alleleassessment_id']
        """

        match = next((e for e in existing_assessments
                        if allele_assessment['allele_id'] == e.allele_id
                            and 'presented_alleleassessment_id' in allele_assessment
                            and allele_assessment['presented_alleleassessment_id'] == e.id),
                     None)
        if not match and error_if_not_found:
            raise ApiError(
                "Found no matching alleleassessment for allele_id: {}, id: {}. Either the assessment is outdated or it doesn't exist.".format(
                    allele_assessment['allele_id'], allele_assessment['presented_alleleassessment_id']))

        return match

    def _create_or_reuse_referenceassessments(self, user_id, referenceassessments):
        if not referenceassessments:
            return list(), list()

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
            assessment.ReferenceAssessment.date_superceeded.is_(None)  # Only allowed to reuse valid assessment
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
                assessment_obj.user_id = user_id

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
                    to_supercede.date_superceeded = datetime.datetime.now(pytz.utc)
                    assessment_obj.previous_assessment_id = to_supercede.id
                created.append(assessment_obj)

        return created, reused

    def _attach_attachments(self, attachments, created_alleleassessments):
        all_attachment_ids = sum([atchmt["attachments"] for atchmt in attachments], [])
        attachment_objs = self.session.query(attachment.Attachment).filter(
            attachment.Attachment.id.in_(all_attachment_ids)
        ).all()

        assert set(all_attachment_ids) == set(a.id for a in attachment_objs), "Not all attachments were found in the database"

        for aa in created_alleleassessments:
            attachment_ids = next(atchmt["attachments"] for atchmt in attachments)
            aa.attachments = [at for at in attachment_objs if at.id in attachment_ids]

