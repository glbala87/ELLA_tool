from __future__ import annotations

from typing import Dict, List, Optional

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
    source: Optional[str]
    value: Optional[List[str]]
    match: Optional[List[str]]
    op: Optional[str]


class ACMGCodeList(BaseModel):
    codes: List[ACMGCode]
