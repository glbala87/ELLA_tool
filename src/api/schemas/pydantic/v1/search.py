from __future__ import annotations

from typing import Optional, List, Any

from api.schemas.pydantic.v1 import BaseModel
from api.schemas.pydantic.v1.alleles import Allele
from api.schemas.pydantic.v1.workflow import AlleleInterpretationOverview


class SearchGene(BaseModel):
    symbol: str
    hgnc_id: int


class SearchUser(BaseModel):
    username: str
    first_name: str
    last_name: str


class SearchOptions(BaseModel):
    gene: Optional[List[SearchGene]]
    user: Optional[List[SearchUser]]


class SearchAllele(BaseModel):
    allele: Allele
    interpretations: List[AlleleInterpretationOverview]


class SearchResults(BaseModel):
    alleles: List[SearchAllele]
    analyses: List[Any]  # TODO
