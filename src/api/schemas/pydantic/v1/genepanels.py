from __future__ import annotations

from typing import List, Optional

from api.schemas.pydantic.v1 import BaseModel
from api.schemas.pydantic.v1.common import GenericID
from api.util.types import GenomeReference, StrandSymbol


class Gene(BaseModel):
    hgnc_id: int
    hgnc_symbol: str


class Transcript(BaseModel):
    transcript_name: str
    gene: Gene


class TranscriptFull(Transcript):
    gene: Gene
    corresponding_refseq: Optional[str]
    corresponding_ensembl: Optional[str]
    corresponding_lrg: Optional[str]
    genome_reference: GenomeReference
    chromosome: str
    tx_start: int
    tx_end: int
    strand: StrandSymbol
    cds_start: Optional[int]
    cds_end: Optional[int]
    exon_starts: List[int]
    exon_ends: List[int]


class TranscriptAlternative(BaseModel):
    id: int
    transcript_name: str
    tags: Optional[List[str]]


class PhenotypeBasic(BaseModel):
    id: int
    inheritance: str


class Phenotype(PhenotypeBasic):
    gene: Gene


class PhenotypeAlternative(PhenotypeBasic):
    description: str


class PhenotypeFull(PhenotypeBasic):
    description: str
    omim_id: int
    gene: Gene


class GenepanelBasic(BaseModel):
    name: str
    version: str


class Genepanel(GenepanelBasic):
    official: bool


# uses Full submodels
class GenepanelFull(Genepanel):
    "Panel of genes connected to a certain analysis"
    transcripts: List[TranscriptFull]
    phenotypes: List[PhenotypeFull]


# uses non-Full submodels
class GenepanelTranscripts(Genepanel):
    "Panel of genes connected to a certain analysis"
    transcripts: List[Transcript]
    phenotypes: List[Phenotype]


class GeneAlternative(Gene):
    phenotypes: List[PhenotypeAlternative]
    transcripts: List[TranscriptAlternative]


class GenepanelSingle(GenepanelBasic):
    genes: List[GeneAlternative]


class GenepanelStats(BaseModel):
    name: str
    version: str
    addition_cnt: int
    overlap_cnv: int
    missing_cnt: int


class NewGenepanelGene(BaseModel):
    transcripts: List[GenericID]
    phenotypes: List[GenericID]


# Put down here to avoid circular import issues with GeneAssessment -> User -> Genepanel
from api.schemas.pydantic.v1.gene_assessments import GeneAssessment  # noqa: E402


class Inheritances(BaseModel):
    inheritance: str
    transcript_name: str
    hgnc_id: int


class GenepanelFullAssessmentsInheritances(GenepanelFull):
    geneassessments: List[GeneAssessment]
    inheritances: List[Inheritances]
