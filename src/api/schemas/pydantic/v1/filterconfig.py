from __future__ import annotations

from api.schemas.pydantic.v1 import BaseModel
from typing import Dict, List, Optional
from api.util.types import FilterNames


class FilterWithoutExceptions(BaseModel):
    name: FilterNames
    config: Dict


class FilterWithExceptions(FilterWithoutExceptions):
    exceptions: Optional[List[FilterWithoutExceptions]] = None


class Filters(BaseModel):
    filters: List[FilterWithExceptions]


class FilterConfig(BaseModel):
    id: int
    name: str
    filterconfig: Filters
    active: bool
    requirements: List
