from __future__ import annotations

from typing import List, Optional

from api.schemas.pydantic.v1 import BaseModel
from api.util.types import ReferenceEvalRelevance

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
    year: Optional[int] = None

    # @classmethod
    # def _meta(cls: Type[Reference]) -> Dict[str, Any]:
    #     # mark fields with default values as required in schema
    #     req_fields = [k for k, v in cls.__fields__.items() if v.required or v.default is not None]
    #     return {"required": req_fields}


# NOTE: should ref assessments be stored in their own file?


class ReferenceEvaluation(BaseModel):
    comment: Optional[str] = None
    sources: Optional[List[str]] = None
    relevance: Optional[ReferenceEvalRelevance] = None
    ref_quality: Optional[Optional[str]] = None
    ref_auth_classification: Optional[Optional[str]] = None
    ref_segregation: Optional[str] = None
    ref_segregation_quality: Optional[str] = None
    ref_ihc: Optional[str] = None
    ref_msi: Optional[str] = None
    ref_prot: Optional[str] = None
    ref_prediction: Optional[Optional[str]] = None
    ref_prot_quality: Optional[str] = None
    ref_population_affecteds: Optional[Optional[str]] = None
    ref_rna: Optional[str] = None
    ref_rna_quality: Optional[str] = None
    ref_aa_overlap: Optional[str] = None
    ref_aa_overlap_same_novel: Optional[str] = None
    ref_domain_overlap: Optional[str] = None
    ref_population_healthy: Optional[Optional[str]] = None
    ref_prediction_tool: Optional[str] = None
    ref_msi_quality: Optional[str] = None
    ref_aa_overlap_aa: Optional[str] = None
    ref_aa_overlap_sim: Optional[str] = None
    ref_aa_overlap_aa_ref: Optional[str] = None
    ref_aa_overlap_quality: Optional[str] = None
    ref_phase: Optional[Optional[str]] = None
    ref_ihc_quality: Optional[str] = None
    ref_domain_benign: Optional[str] = None
    ref_de_novo: Optional[str] = None


class BaseReferenceAssessment(BaseModel):
    allele_id: int
    reference_id: int
    evaluation: ReferenceEvaluation
    analysis_id: Optional[int] = None
    date_superceeded: Optional[str] = None


# TODO: should OptRef... being the default and below StrictRef... ?
#       alternatively, is the stricter model actually needed anywhere?
class ReferenceAssessment(BaseReferenceAssessment):
    id: int
    user_id: int
    date_created: str
    genepanel_name: str
    genepanel_version: str


class OptReferenceAssessment(BaseReferenceAssessment):
    id: Optional[int] = None
    user_id: Optional[int] = None
    date_created: Optional[str] = None
    genepanel_name: Optional[str] = None
    genepanel_version: Optional[str] = None
    reuse: Optional[bool] = None
    reuseCheckedId: Optional[int] = None


class ReusedReferenceAssessment(BaseModel):
    id: int
    allele_id: int
    reference_id: int
    reuse: Optional[bool]
    reuseCheckedId: Optional[int]


class NewReferenceAssessment(BaseModel):
    evaluation: ReferenceEvaluation
    allele_id: int
    reference_id: int
    genepanel_name: Optional[str] = None
    genepanel_version: Optional[str] = None
