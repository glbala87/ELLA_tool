from __future__ import annotations
from typing import List, Optional
from typing_extensions import Literal

from api.schemas.pydantic.v1 import BaseModel, ExtraOK
from pydantic import Field


class IgvSearchItem(BaseModel):
    chromosome: str
    start: int
    end: int


# igv.js handles its own config validation
class IgvConfig(ExtraOK):
    name: Optional[str]
    url: Optional[str]


class TrackConfigBase(BaseModel):
    presets: List[str] = Field(default_factory=list)
    type: Optional[Literal["roi"]]
    show: Optional[bool]
    description: Optional[str]


class TrackConfig(TrackConfigBase):
    applied_rules: List[str] = Field(default_factory=list)
    igv: IgvConfig
    URL: str

    def update_igv(self, cfg: IgvConfig):
        self.igv = IgvConfig(**{**self.igv.dump(exclude_none=True), **cfg.dump(exclude_none=True)})


class TrackConfigDefault(TrackConfigBase):
    limit_to_groups: Optional[List[str]]
    igv: Optional[IgvConfig]
