from __future__ import annotations

from typing import Dict, List

from api.schemas.pydantic.v1 import BaseModel
from pydantic import Field


class ACMGClassification(BaseModel):
    clazz: str = Field(alias="class")
    classification: str
    message: str
    contributors: List[str]
    meta: Dict


class ACMGCode(BaseModel):
    code: str
    source: str
    value: List[str]
    match: List[str]
    op: str
