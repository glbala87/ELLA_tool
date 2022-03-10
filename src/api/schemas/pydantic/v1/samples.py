from __future__ import annotations

from typing import List, Optional

from api.schemas.pydantic.v1 import BaseModel
from api.schemas.pydantic.v1.genotypes import GenotypeSampleData
from api.util.types import SampleSex, SampleType


class Sample(BaseModel):
    "Represents one sample. There can be many samples per analysis."

    id: int
    sex: Optional[SampleSex] = None
    identifier: str
    sample_type: SampleType
    date_deposited: str
    affected: bool
    proband: bool
    family_id: Optional[str] = None
    father_id: Optional[int] = None
    father: Optional[Sample] = None
    mother_id: Optional[int] = None
    mother: Optional[Sample] = None
    sibling_id: Optional[int] = None
    siblings: Optional[List[Sample]] = None
    genotype: Optional[GenotypeSampleData] = None


Sample.update_forward_refs()
