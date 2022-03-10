from __future__ import annotations

from typing import Dict, Optional, List
from api.schemas.pydantic.v1 import BaseModel
from api.schemas.pydantic.v1.workflow_allele_state import AlleleState
from api.schemas.pydantic.v1.users import User
from api.util.types import (
    AlleleInterpretationWorkflowStatus,
    AnalysisInterpretationWorkflowStatus,
    InterpretationStatus,
    WorkflowStatus,
    WorkflowTypes,
)


class Report(BaseModel):
    included: bool


class Workflow(BaseModel):
    reviewed: bool


class InterpretationBase(BaseModel):
    id: int
    status: InterpretationStatus
    # NOTE: no default set in InterpretationMixin.finalized. Is there a difference between None and False?
    finalized: Optional[bool] = None
    date_last_update: str
    genepanel_name: str
    genepanel_version: str
    user: Optional[User] = None
    user_id: Optional[int] = None


class InterpretationSnapshot(BaseModel):
    "snapshot of a allele interpretation with context"
    id: int
    allele_id: int
    alleleassessment_id: Optional[int] = None
    allelereport_id: Optional[int] = None
    annotation_id: Optional[int] = None
    customannotation_id: Optional[int] = None
    date_created: str


class AlleleCollision(BaseModel):
    type: WorkflowTypes
    user: Optional[User]
    allele_id: int
    analysis_name: str
    analysis_id: int
    workflow_status: WorkflowStatus


class OngoingWorkflow(BaseModel):
    user_id: int
    workflow_status: WorkflowStatus
    allele_id: int
    analysis_id: Optional[int]


# Allele Workflow


class ReportComment(BaseModel):
    comment: Optional[str]
    indicationscomment: Optional[str]


class AlleleInterpretationState(BaseModel):
    allele: Optional[Dict[str, AlleleState]]
    manuallyAddedAlleles: Optional[List[int]]
    filterconfigId: Optional[int]
    report: Optional[ReportComment]


class AlleleInterpretationBase(InterpretationBase):
    workflow_status: AlleleInterpretationWorkflowStatus


# Ref datamodel.workflow.AlleleInterpretation, schemas.alleleinterpretations.AlleleInterpretationSchema
class AlleleInterpretation(AlleleInterpretationBase):
    "Represents one round of interpretation of an allele"
    state: Optional[AlleleInterpretationState]
    user_state: Optional[Dict]
    date_created: str


class AlleleInterpretationOverview(AlleleInterpretationBase):
    "Represents one round of interpretation of an allele. Overview data fields only."
    allele_id: int


class AlleleInterpretationSnapshot(InterpretationSnapshot):
    "snapshot of a allele interpretation with context"
    alleleinterpretation_id: int


# Analysis Workflow


class AnalysisInterpretationBase(InterpretationBase):
    workflow_status: AnalysisInterpretationWorkflowStatus


class AnalysisInterpretation(AnalysisInterpretationBase):
    "Represents one round of interpretation of an analysis"
    state: Optional[AlleleInterpretationState]
    user_state: Optional[Dict]
    date_created: Optional[str] = None


class AnalysisInterpretationOverview(AnalysisInterpretationBase):
    "Represents one round of interpretation of an analysis. Overview data fields only."
    analysis_id: int


class AnalysisInterpretationSnapshot(InterpretationSnapshot):
    "snapshot of a allele interpretation with context"
    analysisinterpretation_id: int
