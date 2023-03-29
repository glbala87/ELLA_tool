from __future__ import annotations

from typing import Optional

from api.schemas.pydantic.v1 import BaseModel
from api.schemas.pydantic.v1.common import Comment
from api.schemas.pydantic.v1.users import User
from typing_extensions import Literal


class AlleleReportsUsergroup(BaseModel):
    id: int
    name: str


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
    evaluation: Optional[Comment] = None


class ReusedAlleleReport(BaseModel):
    reuse: Literal[True]
    allele_id: int
    presented_allelereport_id: int


class NewAlleleReport(BaseModel):
    evaluation: Comment
    allele_id: int
    presented_allelereport_id: Optional[int] = None
    reuse: Literal[False]
