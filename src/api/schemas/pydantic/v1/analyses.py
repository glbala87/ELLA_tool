from __future__ import annotations

from typing import List, Optional

from api.schemas.pydantic.v1 import BaseModel
from api.schemas.pydantic.v1.genepanels import Genepanel
from api.schemas.pydantic.v1.samples import Sample
from api.schemas.pydantic.v1.workflow import AnalysisInterpretationOverview
from pydantic import Field


class AnalysisIdName(BaseModel):
    id: int
    name: str


class AnalysisStats(BaseModel):
    allele_count: int


class Analysis(BaseModel):
    id: int
    name: str
    date_requested: Optional[str]
    date_deposited: str
    interpretations: List[AnalysisInterpretationOverview] = Field(default_factory=list)
    genepanel: Genepanel
    samples: List[Sample]
    report: Optional[str] = None
    warnings: Optional[str] = None
    attachments: List[str] = Field(default_factory=list)


class OverviewAnalysis(Analysis):
    priority: int
    review_comment: Optional[str] = None
    warning_cleared: Optional[bool] = None
