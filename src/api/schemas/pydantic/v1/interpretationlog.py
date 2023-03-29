from __future__ import annotations

from typing import Any, Dict, List, Optional

from api.schemas.pydantic.v1 import BaseModel
from pydantic import Field, root_validator


class LogAssessment(BaseModel):
    allele_id: int
    hgvsc: str
    classification: str
    previous_classification: Optional[List[str]] = None


class LogReport(BaseModel):
    allele_id: int
    hgvsc: str


class CreateInterpretationLog(BaseModel):
    message: Optional[str] = None
    warning_cleared: Optional[bool] = None
    priority: Optional[int] = None
    review_comment: Optional[str] = None

    @root_validator
    def has_content(cls, values: Dict[str, Any]):
        if any(values.get(a) is not None for a in cls.__fields__):
            return values
        raise ValueError(f"Must specify at least one of: {', '.join(cls.__fields__.keys())}")


class InterpretationLog(CreateInterpretationLog):
    "Represents one interpretation log item."
    id: int
    date_created: str
    user_id: Optional[int] = None
    alleleassessment: Dict = Field(default_factory=dict)  # LogAssessment, but empty dict allowed
    allelereport: Dict = Field(default_factory=dict)  # LogReport, but empty dict allowed
    editable: bool
