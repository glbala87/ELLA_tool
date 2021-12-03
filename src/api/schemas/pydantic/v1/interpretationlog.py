from __future__ import annotations
from typing import Optional

from api.schemas.pydantic.v1 import BaseModel


class InterpretationLog(BaseModel):
    "Represents one interpretation log item."
    id: int
    date_created: str
    message: str
    warning_cleared: bool
    review_comment: Optional[str] = None
    user_id: Optional[int] = None
    priority: Optional[int] = None
    alleleassessment_id: int
    allelereport_id: int
