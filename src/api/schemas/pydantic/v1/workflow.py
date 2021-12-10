from __future__ import annotations

from typing import Dict, Optional

from api.schemas.pydantic.v1 import BaseModel
from api.schemas.pydantic.v1.users import User
from api.util.types import (
    AlleleInterpretationWorkflowStatus,
    InterpretationStatus,
    WorkflowStatus,
    WorkflowTypes,
)


class AlleleInterpretationSnapshot(BaseModel):
    "snapshot of a allele interpretation with context"
    id: int
    date_created: str
    allele_id: int
    alleleinterpretation_id: int
    annotation_id: Optional[int] = None
    customannotation_id: Optional[int] = None
    alleleassessment_id: Optional[int] = None
    allelereport_id: Optional[int] = None


# Ref datamodel.workflow.AlleleInterpretation, schemas.alleleinterpretations.AlleleInterpretationSchema
class AlleleInterpretation(BaseModel):
    "Represents one round of interpretation of an allele"
    id: int
    status: InterpretationStatus
    # NOTE: no default set in InterpretationMixin.finalized. Is there a difference between None and False?
    finalized: Optional[bool] = None
    workflow_status: AlleleInterpretationWorkflowStatus
    user_state: Dict
    state: Dict
    genepanel_name: str
    genepanel_version: str
    date_last_update: str
    date_created: str
    # NOTE: None/null found for these in test data. Is this behavior seen in production?
    user_id: Optional[int] = None
    user: Optional[User] = None


class AlleleInterpretationOverview(BaseModel):
    "Represents one round of interpretation of an allele. Overview data fields only."
    id: int
    status: InterpretationStatus
    finalized: bool
    workflow_status: AlleleInterpretationWorkflowStatus
    allele_id: int
    genepanel_name: str
    genepanel_version: str
    date_last_update: str
    user_id: int
    user: User


class AlleleCollision(BaseModel):
    workflow_type: WorkflowTypes
    user: Optional[User]
    allele_id: int
    analysis_name: str
    analysis_id: int
    workflow_status: WorkflowStatus
