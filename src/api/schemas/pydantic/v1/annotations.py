from __future__ import annotations

from enum import Enum
from typing import Dict, List, Optional

from api.schemas.pydantic.v1 import BaseModel, ExtraOK, Field, IntDict, YesNo
from api.schemas.pydantic.v1.references import AnnotationReference
from typing_extensions import Literal

Strand = Literal[-1, 1]
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


class Consequence(Enum):
    transcript_ablation = "transcript_ablation"
    splice_donor_variant = "splice_donor_variant"
    splice_acceptor_variant = "splice_acceptor_variant"
    stop_gained = "stop_gained"
    frameshift_variant = "frameshift_variant"
    start_lost = "start_lost"
    initiator_codon_variant = "initiator_codon_variant"
    stop_lost = "stop_lost"
    inframe_insertion = "inframe_insertion"
    inframe_deletion = "inframe_deletion"
    missense_variant = "missense_variant"
    protein_altering_variant = "protein_altering_variant"
    transcript_amplification = "transcript_amplification"
    splice_region_variant = "splice_region_variant"
    incomplete_terminal_codon_variant = "incomplete_terminal_codon_variant"
    synonymous_variant = "synonymous_variant"
    start_retained_variant = "start_retained_variant"
    stop_retained_variant = "stop_retained_variant"
    coding_sequence_variant = "coding_sequence_variant"
    mature_miRNA_variant = "mature_miRNA_variant"
    field_5_prime_UTR_variant = "5_prime_UTR_variant"
    field_3_prime_UTR_variant = "3_prime_UTR_variant"
    non_coding_transcript_exon_variant = "non_coding_transcript_exon_variant"
    non_coding_transcript_variant = "non_coding_transcript_variant"
    intron_variant = "intron_variant"
    NMD_transcript_variant = "NMD_transcript_variant"
    upstream_gene_variant = "upstream_gene_variant"
    downstream_gene_variant = "downstream_gene_variant"
    TFBS_ablation = "TFBS_ablation"
    TFBS_amplification = "TFBS_amplification"
    TF_binding_site_variant = "TF_binding_site_variant"
    regulatory_region_variant = "regulatory_region_variant"
    regulatory_region_ablation = "regulatory_region_ablation"
    regulatory_region_amplification = "regulatory_region_amplification"
    feature_elongation = "feature_elongation"
    feature_truncation = "feature_truncation"
    intergenic_variant = "intergenic_variant"


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
class Annotation(ExtraOK):
    references: Optional[List[AnnotationReference]] = None
    frequencies: Optional[Dict[str, Frequency]] = None
    transcripts: Optional[List[Transcript]] = None
