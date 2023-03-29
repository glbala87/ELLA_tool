import datetime
from dataclasses import dataclass, field
import pytz
from typing import Sequence, Dict, Optional, List, Tuple
from vardb.datamodel import assessment, sample, attachment


from api.schemas import AlleleAssessmentSchema, ReferenceAssessmentSchema
from api import ApiError

import logging

log = logging.getLogger(__name__)


@dataclass
class AssessmentCreatorResult:
    created_alleleassessment: Optional[assessment.AlleleAssessment]
    reused_alleleassessment: Optional[assessment.AlleleAssessment]
    created_referenceassessments: List[assessment.ReferenceAssessment] = field(default_factory=list)
    reused_referenceassessments: List[assessment.ReferenceAssessment] = field(default_factory=list)

    @property
    def alleleassessment(self) -> Optional[assessment.AlleleAssessment]:
        return self.created_alleleassessment or self.reused_alleleassessment

    @property
    def referenceassessments(self) -> List[assessment.ReferenceAssessment]:
        return self.created_referenceassessments + self.reused_referenceassessments


class AssessmentCreator(object):
    def __init__(self, session):
        self.session = session

    def create_from_data(
        self,
        user_id: int,
        usergroup_id: int,
        allele_id: int,
        annotation_id: int,
        custom_annotation_id: Optional[int],
        genepanel_name: str,
        genepanel_version: str,
        alleleassessment: Dict,
        referenceassessments: Optional[Sequence[Dict]],
        analysis_id: int = None,
    ) -> AssessmentCreatorResult:
        """
        Takes in alleleassessment/referenceassessment data and (if not reused),
        creates new assessment objects.

        The created objects are not added to session/database.
        """

        # Pydantic models converted to dict may have the key, but no value. Use the provided in that case
        for sub_dict in [alleleassessment, *(referenceassessments or [])]:
            if sub_dict.get("genepanel_name") is None:
                sub_dict["genepanel_name"] = genepanel_name
            if sub_dict.get("genepanel_version") is None:
                sub_dict["genepanel_version"] = genepanel_version

        ra_created, ra_reused = self._create_or_reuse_referenceassessments(
            allele_id,
            user_id,
            usergroup_id,
            genepanel_name,
            genepanel_version,
            referenceassessments,
            analysis_id=analysis_id,
        )

        aa, reused = self._create_or_reuse_alleleassessment(
            allele_id,
            user_id,
            usergroup_id,
            annotation_id,
            genepanel_name,
            genepanel_version,
            alleleassessment,
            custom_annotation_id=custom_annotation_id,
            referenceassessments=ra_created + ra_reused,
            analysis_id=analysis_id,
        )

        return AssessmentCreatorResult(
            aa if not reused else None, aa if reused else None, ra_created, ra_reused
        )

    def _create_or_reuse_alleleassessment(
        self,
        allele_id: int,
        user_id: int,
        usergroup_id: int,
        annotation_id: int,
        genepanel_name: str,
        genepanel_version: str,
        alleleassessment: Dict,
        custom_annotation_id: int = None,
        referenceassessments: Sequence[Dict] = None,
        analysis_id: int = None,
    ) -> Tuple[assessment.AlleleAssessment, bool]:
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

        # If existing, check that user saw the current previous version
        if existing_assessment:
            presented_id = alleleassessment["presented_alleleassessment_id"]
            if presented_id != existing_assessment.id:
                raise ApiError(
                    f"'presented_alleleassessment_id': {presented_id} does not match latest existing alleleassessment id: {existing_assessment.id}"
                )

        if alleleassessment.get("reuse"):
            assert existing_assessment
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
            assessment_obj.usergroup_id = usergroup_id
            assessment_obj.referenceassessments = referenceassessments
            assessment_obj.annotation_id = annotation_id
            assessment_obj.genepanel_name = genepanel_name
            assessment_obj.genepanel_version = genepanel_version
            assessment_obj.custom_annotation_id = custom_annotation_id

            if analysis:
                assessment_obj.analysis_id = analysis_id

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
        self,
        allele_id: int,
        user_id: int,
        usergroup_id: int,
        genepanel_name: str,
        genepanel_version: str,
        referenceassessments: Optional[Sequence[dict]],
        analysis_id: int = None,
    ) -> Tuple[List[assessment.ReferenceAssessment], List[assessment.ReferenceAssessment]]:
        if not referenceassessments:
            return list(), list()

        analysis: Optional[sample.Analysis] = None
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
                assessment_obj.usergroup_id = usergroup_id
                assessment_obj.genepanel_name = genepanel_name
                assessment_obj.genepanel_version = genepanel_version

                if analysis:
                    assessment_obj.analysis_id = analysis_id

                # Check if there's an existing assessment for this allele/reference. If so, we want to supercede it
                to_supercede = next(
                    (e for e in existing if ra["reference_id"] == e.reference_id), None
                )
                if to_supercede:
                    to_supercede.date_superceeded = datetime.datetime.now(pytz.utc)
                    assessment_obj.previous_assessment_id = to_supercede.id
                created.append(assessment_obj)

        return created, reused
