from __future__ import annotations

from typing import Dict, List, Optional

from api.schemas.pydantic.v1 import BaseModel
from api.schemas.pydantic.v1.common import Comment
from api.schemas.pydantic.v1.references import ReferenceAssessment
from api.schemas.pydantic.v1.users import User
from api.util.types import AlleleAssessmentClassification
from typing_extensions import Literal


class IncludedItem(BaseModel):
    op: Optional[str]
    code: str
    uuid: str
    match: Optional[List[str]]
    source: Optional[str]
    comment: str


class SuggestedItem(BaseModel):
    op: Optional[str]
    code: str
    match: Optional[List[str]]
    source: Optional[str]


class SuggestedAcmg(BaseModel):
    included: Optional[List[IncludedItem]] = None
    suggested: Optional[List[SuggestedItem]] = None
    suggested_classification: Optional[Optional[int]] = None


class AlleleAssessmentEvaluation(BaseModel):
    acmg: SuggestedAcmg
    comment: Optional[str]
    external: Comment
    frequency: Comment
    reference: Comment
    prediction: Comment
    classification: Comment
    similar: Optional[Comment] = None


class AlleleAssessmentUsergroup(BaseModel):
    id: int
    name: str


class AlleleAssessmentOverview(BaseModel):
    "Represents an assessment of one allele for overview"

    id: int
    date_created: str
    classification: AlleleAssessmentClassification


class AlleleAssessment(BaseModel):
    "Represents an assessment of one allele"
    id: int
    date_created: str
    date_superceeded: Optional[str] = None
    allele_id: int
    analysis_id: Optional[int] = None
    genepanel_name: str
    genepanel_version: str
    annotation_id: Optional[int] = None
    custom_annotation_id: Optional[int] = None
    previous_assessment_id: Optional[int] = None
    user_id: int
    usergroup_id: Optional[int] = None
    usergroup: Optional[AlleleAssessmentUsergroup] = None
    user: User
    classification: AlleleAssessmentClassification
    seconds_since_update: int
    evaluation: AlleleAssessmentEvaluation
    attachment_ids: Optional[List[int]] = None


class AlleleAssessmentInput(BaseModel):
    "Represents data to create an allele assessment"

    allele_id: int
    analysis_id: int
    genepanel_name: str
    genepanel_version: str
    classification: AlleleAssessmentClassification
    evaluation: Optional[Dict] = None
    referenceassessments: Optional[List[ReferenceAssessment]] = None


class ReusedAlleleAssessment(BaseModel):
    reuse: Literal[True]
    allele_id: int
    presented_alleleassessment_id: int


class NewAlleleAssessment(BaseModel):
    reuse: Literal[False]
    reuseCheckedId: Optional[int] = None
    allele_id: int
    attachment_ids: List[int]
    classification: AlleleAssessmentClassification
    evaluation: AlleleAssessmentEvaluation
    genepanel_name: Optional[str] = None
    genepanel_version: Optional[str] = None
    presented_alleleassessment_id: Optional[int] = None
