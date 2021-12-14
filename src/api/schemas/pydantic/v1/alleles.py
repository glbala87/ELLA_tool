from __future__ import annotations

from typing import List, Optional, Union

from api.schemas.pydantic.v1 import BaseModel
from api.schemas.pydantic.v1.allele_assessments import AlleleAssessment, AlleleAssessmentOverview
from api.schemas.pydantic.v1.allele_reports import AlleleReport
from api.schemas.pydantic.v1.annotations import Annotation
from api.schemas.pydantic.v1.genepanels import GenepanelBasic
from api.schemas.pydantic.v1.references import ReferenceAssessment
from api.schemas.pydantic.v1.samples import Sample
from api.schemas.pydantic.v1.workflow import AlleleInterpretationOverview
from api.util.types import GenomeReference
from pydantic import Field


class Warnings(BaseModel):
    worse_consequence: str


class Allele(BaseModel):
    length: int
    genome_reference: GenomeReference
    vcf_ref: str
    change_from: str
    change_to: str
    chromosome: str
    start_position: int
    change_type: str
    open_end_position: int
    vcf_pos: int
    vcf_alt: str
    id: int
    caller_type: str
    annotation: Annotation
    tags: List[str]
    warnings: Optional[Warnings] = None
    reference_assessments: List[ReferenceAssessment] = Field(default_factory=list)
    allele_assessment: Optional[Union[AlleleAssessmentOverview, AlleleAssessment]] = None
    allele_report: Optional[AlleleReport] = None
    samples: Optional[List[Sample]] = None


class AlleleOverview(BaseModel):
    genepanel: GenepanelBasic
    allele: Allele
    date_created: str
    priority: int
    review_comment: Optional[str] = None
    interpretations: List[AlleleInterpretationOverview]
