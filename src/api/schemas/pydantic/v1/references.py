from __future__ import annotations

from enum import Enum
from typing import List, Optional

from api.schemas.pydantic.v1 import BaseModel


class Relevance(str, Enum):
    YES = "Yes"
    NO = "No"
    IGNORE = "Ignore"


###


class AnnotationReference(BaseModel):
    id: Optional[int] = None
    pubmed_id: Optional[int] = None
    source: str
    source_info: Optional[str] = None


class Reference(BaseModel):
    id: int
    authors: Optional[str] = None
    title: Optional[str] = None
    journal: Optional[str] = None
    abstract: Optional[str] = None
    pubmed_id: int
    published: bool = True


# NOTE: should ref assessments be stored in their own file?


class ReferenceEvaluation(BaseModel):
    comment: str
    sources: List[str]
    ref_prot: Optional[str] = None
    relevance: Relevance
    ref_prot_quality: Optional[str] = None
    ref_auth_classification: Optional[str] = None
    ref_population_affecteds: Optional[str] = None
    ref_phase: Optional[str] = None
    ref_quality: Optional[str] = None


class ReferenceAssessment(BaseModel):
    id: int
    user_id: int
    allele_id: int
    reference_id: int
    analysis_id: Optional[int] = None
    date_created: str
    date_superceeded: Optional[str] = None
    genepanel_name: str
    genepanel_version: str
    evaluation: ReferenceEvaluation
