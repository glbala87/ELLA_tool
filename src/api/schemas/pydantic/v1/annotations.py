from __future__ import annotations

from typing import Dict, List, Optional

from api.schemas.pydantic.v1 import BaseModel, ExtraOK, Field
from api.schemas.pydantic.v1.references import AnnotationReference
from api.util.types import IntDict, Strand, YesNo, Consequence

rank_pattern = r"[1-9]\d*/[1-9]\d*"
# NOTE: these are not enforced by pydantic, but it keeps them in the schema spec like they were before
freq_props = {"[a-zA-Z]*": {"type": "number", "minimum": 0, "maximum": 1.0}}
count_props = {"[a-zA-Z]*": {"type": "integer", "minimum": 0}}
filter_props = {"[a-zA-Z]+": {"type": "array", "items": {"type": "string"}}}


class Frequency(BaseModel):
    freq: Dict[str, float] = Field(..., patternProperties=freq_props)
    count: Optional[IntDict] = Field(None, patternProperties=count_props)
    hom: Optional[IntDict] = Field(None, patternProperties=count_props)
    hemi: Optional[IntDict] = Field(None, patternProperties=count_props)
    het: Optional[IntDict] = Field(None, patternProperties=count_props)
    num: Optional[IntDict] = Field(None, patternProperties=count_props)
    filter: Optional[Dict[str, List[str]]] = Field(None, patternProperties=filter_props)
    indications: Optional[Dict[str, IntDict]] = None


class Transcript(BaseModel):
    consequences: List[Consequence]
    hgnc_id: Optional[int] = None
    symbol: Optional[str] = None
    HGVSc: Optional[str] = None
    HGVSc_short: Optional[str] = None
    HGVSc_insertion: Optional[str] = None
    HGVSp: Optional[str] = None
    protein: Optional[str] = None
    strand: Strand
    amino_acids: Optional[str] = None
    dbsnp: Optional[List[str]] = None
    exon: Optional[str] = Field(None, regex=rank_pattern)
    intron: Optional[str] = Field(None, regex=rank_pattern)
    codons: Optional[str] = None
    transcript: str
    is_canonical: bool
    exon_distance: Optional[int] = None
    coding_region_distance: Optional[int] = None
    in_last_exon: YesNo
    splice: Optional[List] = None


# minimal model schema from: src/vardb/datamodel/jsonschemas/annotation_v1.json
# + marshmallow schema: src/api/schemas/annotations.py:AnnotationSchema
class Annotation(ExtraOK):
    annotation_id: int
    schema_version: str
    annotation_config_id: int
    date_superceeded: Optional[str] = None
    annotations: Optional[List[Dict]] = None
    references: Optional[List[AnnotationReference]] = None
    frequencies: Optional[Dict[str, Frequency]] = None
    transcripts: Optional[List[Transcript]] = None


class AnnotationConfig(BaseModel):
    id: int
    view: List[Dict]
    # not included in AnnotationConfigSchema, but are in datamodel
    deposit: Optional[Dict] = None
    date_created: Optional[str] = None
