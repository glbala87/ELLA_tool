from __future__ import annotations

from enum import Enum
from typing import Dict, List, Optional

from api.schemas.pydantic.v1 import BaseModel, Field
from api.schemas.pydantic.v1.references import ReferenceAssessment
from api.schemas.pydantic.v1.users import User


class AlleleAssessmentClassification(str, Enum):
    ONE = "1"
    TWO = "2"
    THREE = "3"
    FOUR = "4"
    FIVE = "5"
    NP = "NP"
    RF = "RF"
    DR = "DR"


class AlleleAssessmentUsergroup(BaseModel):
    id: int
    name: str


class AlleleAssessmentOver(BaseModel):
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
    usergroup_id: int
    usergroup: AlleleAssessmentUsergroup
    user: User
    classification: AlleleAssessmentClassification
    seconds_since_update: int
    evaluation: Dict = Field(default_factory=dict)
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
