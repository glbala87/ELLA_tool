import datetime
import pytz
from typing import Sequence, Dict, Optional
from vardb.datamodel import assessment, sample, attachment


from api.schemas import AlleleAssessmentSchema, ReferenceAssessmentSchema
from api import ApiError

import logging

logging.basicConfig(level=logging.DEBUG)
log = logging.getLogger(__name__)


class AssessmentCreator(object):
    def __init__(self, session):
        self.session = session

    def create_from_data(
        self,
        user_id: int,
        allele_id: int,
        annotation_id: int,
        alleleassessment: Dict,
        custom_annotation_id: int = None,
        referenceassessments: Sequence[Dict] = None,
        analysis_id: int = None,
    ):
        """
        Takes in alleleassessment/referenceassessment data and (if not reused),
        creates new assessment objects in database.

        Returns the alleleassessment/referenceassessments, along with a flag whether it was created or reused.

        ReferenceAssessments are connected to the AlleleAssessment.
        """

        ra_created, ra_reused = self._create_or_reuse_referenceassessments(
            allele_id, user_id, referenceassessments, analysis_id=analysis_id
        )

        aa, reused = self._create_or_reuse_alleleassessment(
            allele_id,
            user_id,
            annotation_id,
            alleleassessment,
            custom_annotation_id=custom_annotation_id,
            referenceassessments=ra_created + ra_reused,
            analysis_id=analysis_id,
        )

        return {
            "referenceassessments": {"reused": ra_reused, "created": ra_created},
            "alleleassessment": {
                "reused": aa if reused else None,
                "created": aa if not reused else None,
            },
        }

    def _create_or_reuse_alleleassessment(
        self,
        allele_id: int,
        user_id: int,
        annotation_id: int,
        alleleassessment: Dict,
        custom_annotation_id: int = None,
        referenceassessments: Sequence[Dict] = None,
        analysis_id: int = None,
    ):
        assert alleleassessment["allele_id"] == allele_id

        analysis: Optional[sample.Analysis] = None
        if analysis_id:
            analysis = (
                self.session.query(sample.Analysis).filter(sample.Analysis.id == analysis_id).one()
            )

        existing_assessment = (
            self.session.query(assessment.AlleleAssessment)
            .filter(
                assessment.AlleleAssessment.allele_id == allele_id,
                assessment.AlleleAssessment.date_superceeded.is_(
                    None
                ),  # Only allowed to reuse valid assessment
            )
            .one_or_none()
        )

        result_alleleassessment = None
        result_reused = False

        if alleleassessment.get("reuse"):
            assert existing_assessment
            # check that user saw the current previous version
            assert alleleassessment["presented_alleleassessment_id"] == existing_assessment.id
            result_reused = True
            log.debug("Reused assessment %s for allele %s", existing_assessment.id, allele_id)
            result_alleleassessment = existing_assessment

        else:  # create a new assessment
            result_reused = False
            assert "id" not in alleleassessment
            # attachment_ids are not part of internal alleleassessment schema
            attachment_ids = alleleassessment.pop("attachment_ids")
            assessment_obj = AlleleAssessmentSchema(strict=True).load(alleleassessment).data
            assessment_obj.user_id = user_id
            assessment_obj.referenceassessments = referenceassessments
            assessment_obj.annotation_id = annotation_id
            assessment_obj.custom_annotation_id = custom_annotation_id

            # If analysis_id provided, link assessment to genepanel through analysis for safety
            # If not analysis_id, genepanel was loaded using schema above.
            # (analysis_id is loaded through schema)
            if analysis:
                assert assessment_obj.analysis_id == analysis_id
                assessment_obj.genepanel_name = analysis.genepanel_name
                assessment_obj.genepanel_version = analysis.genepanel_version
            elif not (
                "genepanel_name" in alleleassessment and "genepanel_version" in alleleassessment
            ):
                raise ApiError(
                    "No 'analysis_id' and no 'genepanel_name' + 'genepanel_version' given for assessment"
                )

            # If there's an existing assessment for this allele, we want to supercede it
            if existing_assessment:
                existing_assessment.date_superceeded = datetime.datetime.now(pytz.utc)
                assessment_obj.previous_assessment_id = existing_assessment.id

            # Attach attachments
            attachment_objs = (
                self.session.query(attachment.Attachment)
                .filter(attachment.Attachment.id.in_(attachment_ids))
                .all()
            )

            assessment_obj.attachments = attachment_objs

            log.debug(
                "Created assessment for allele: %s, it supercedes: %s",
                assessment_obj.allele_id,
                assessment_obj.previous_assessment_id,
            )

            result_alleleassessment = assessment_obj

        return result_alleleassessment, result_reused

    def _create_or_reuse_referenceassessments(
        self, allele_id, user_id, referenceassessments, analysis_id=None
    ):
        if not referenceassessments:
            return list(), list()

        analysis: sample.Analysis = None
        if analysis_id:
            analysis = (
                self.session.query(sample.Analysis).filter(sample.Analysis.id == analysis_id).one()
            )

        reference_ids = [ra["reference_id"] for ra in referenceassessments]

        existing = (
            self.session.query(assessment.ReferenceAssessment)
            .filter(
                assessment.ReferenceAssessment.allele_id == allele_id,
                assessment.ReferenceAssessment.reference_id.in_(reference_ids),
                assessment.ReferenceAssessment.date_superceeded.is_(
                    None
                ),  # Only allowed to reuse valid assessment
            )
            .all()
        )

        reused = list()
        created = list()
        # When an 'id' is provided, we check and reuse that assessment instead of creating it
        for ra in referenceassessments:
            if "id" in ra:
                to_reuse = next((e for e in existing if ra["id"] == e.id), None)
                if not to_reuse:
                    raise ApiError(
                        "Found no matching referenceassessment for allele_id: {}, reference_id: {}, id: {}. Either the assessment is outdated or it doesn't exist.".format(
                            ra["allele_id"], ra["reference_id"], ra["id"]
                        )
                    )
                reused.append(to_reuse)
            else:
                assessment_obj = ReferenceAssessmentSchema(strict=True).load(ra).data
                assessment_obj.user_id = user_id

                # Link assessment to genepanel through analysis
                if analysis:
                    assert assessment_obj.analysis_id == analysis_id
                    assessment_obj.genepanel_name = analysis.genepanel_name
                    assessment_obj.genepanel_version = analysis.genepanel_version
                elif not ("genepanel_name" in ra and "genepanel_version" in ra):
                    raise ApiError(
                        "No 'analysis_id' and no 'genepanel_name' + 'genepanel_version' given for referenceassessment"
                    )

                # Check if there's an existing assessment for this allele/reference. If so, we want to supercede it
                to_supercede = next(
                    (e for e in existing if ra["reference_id"] == e.reference_id), None
                )
                if to_supercede:
                    to_supercede.date_superceeded = datetime.datetime.now(pytz.utc)
                    assessment_obj.previous_assessment_id = to_supercede.id
                created.append(assessment_obj)

        return created, reused
