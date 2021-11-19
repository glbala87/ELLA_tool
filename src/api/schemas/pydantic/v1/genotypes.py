from __future__ import annotations

from enum import Enum
from typing import Dict, Optional

from api.schemas.pydantic.v1 import BaseModel, ExtraOK, Field


class GenotypeType(str, Enum):
    HOMOZYGOUS = "Homozygous"
    HETEROZYGOUS = "Heterozygous"
    REFERENCE = "Reference"
    NO_COVERAGE = "No coverage"


class Genotype(BaseModel):
    id: int
    variant_quality: int
    filter_status: str


# TODO: get definitive data schema (as returned from AlleleDataLoader), in the meantime allow
#       extra fields as needed
class GenotypeSampleData(ExtraOK):
    id: int
    type: GenotypeType
    multiallelic: bool
    genotype_quality: Optional[int] = None
    sequencing_depth: Optional[int] = None
    allele_depth: Dict = Field(default_factory=dict)
    copy_number: Optional[int] = None
