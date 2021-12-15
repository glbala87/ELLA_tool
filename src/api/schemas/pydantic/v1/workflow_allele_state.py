from __future__ import annotations

from typing import Any, List, Optional
from api.schemas.pydantic.v1.allele_assessments import SuggestedAcmg
from api.schemas.pydantic.v1.references import OptReferenceAssessment
from api.schemas.pydantic.v1.common import Comment
from pydantic import BaseModel


class Report(BaseModel):
    included: bool


class Analysis(BaseModel):
    comment: Optional[str] = None
    notrelevant: Optional[Optional[bool]] = None
    verification: Optional[str]


class Workflow(BaseModel):
    reviewed: bool


class Allelereport(BaseModel):
    evaluation: Comment
    copiedFromId: Optional[int] = None


class StateEvaluation(BaseModel):
    acmg: SuggestedAcmg
    external: Optional[Comment] = None
    frequency: Optional[Comment] = None
    reference: Optional[Comment] = None
    prediction: Optional[Comment] = None
    classification: Optional[Comment] = None
    similar: Optional[Comment] = None


class StateAlleleassessment(BaseModel):
    evaluation: Optional[StateEvaluation] = None
    attachment_ids: Optional[List[int]] = None
    classification: Optional[Optional[str]] = None
    reuse: Optional[bool] = None
    allele_id: Optional[int] = None
    reuseCheckedId: Optional[int] = None


class AlleleState(BaseModel):
    allele_id: int
    alleleassessment: StateAlleleassessment
    alleleAssessmentCopiedFromId: Optional[int] = None
    allelereport: Allelereport
    alleleReportCopiedFromId: Optional[int] = None
    analysis: Optional[Analysis] = None
    autoReuseAlleleAssessmentCheckedId: Optional[int] = None
    presented_alleleassessment_id: Optional[int] = None
    presented_allelereport_id: Optional[int] = None
    quality: Optional[Comment] = None
    referenceassessments: List[OptReferenceAssessment]
    report: Optional[Report] = None
    verification: Optional[Any] = None
    workflow: Optional[Workflow] = None
