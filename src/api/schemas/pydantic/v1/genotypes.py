from __future__ import annotations

from typing import Dict, Optional, List

from api.schemas.pydantic.v1 import BaseModel, ExtraOK
from api.util.types import GenotypeTypes
from pydantic import Field


class Genotype(BaseModel):
    id: int
    variant_quality: int
    filter_status: str


# TODO: get definitive data schema (as returned from AlleleDataLoader), in the meantime allow
#       extra fields as needed
class GenotypeSampleData(ExtraOK):
    id: int
    type: GenotypeTypes
    multiallelic: bool
    genotype_quality: Optional[int] = None
    genotype_likelihood: List[int] = Field(default_factory=list)
    sequencing_depth: Optional[int] = None
    allele_depth: Dict = Field(default_factory=dict)
    copy_number: Optional[int] = None
