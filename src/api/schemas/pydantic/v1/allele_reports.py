from __future__ import annotations

from typing import Optional

from api.schemas.pydantic.v1 import BaseModel
from api.schemas.pydantic.v1.users import User


class AlleleReportsUsergroup(BaseModel):
    id: int
    name: str


class AlleleReportEvaluation(BaseModel):
    comment: str


class AlleleReport(BaseModel):
    "Represents a clinical report for one allele"

    id: int
    date_created: str
    date_superceeded: Optional[str] = None
    allele_id: int
    analysis_id: Optional[int] = None
    previous_report_id: Optional[int] = None
    user_id: int
    usergroup_id: int
    usergroup: AlleleReportsUsergroup
    user: User
    seconds_since_update: int
    evaluation: Optional[AlleleReportEvaluation] = None
