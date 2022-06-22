from __future__ import annotations

from enum import Enum, IntFlag, auto
from typing import Any, Dict, List, NamedTuple, TypeVar, Union

from typing_extensions import Literal


class StrEnum(str, Enum):
    def __str__(self) -> str:
        return self.value

    def __repr__(self) -> str:
        return self.value

    @staticmethod
    def _generate_next_value_(name: str, start: int, count: int, last_values: List[Any]) -> str:
        # sets how auto() generates the value from the given name
        return name.lower()


class BitFlag(IntFlag):
    @property
    def contents(self):
        "returns a list of class members"
        if self.is_compound:
            all_flags = [f for f in self.__class__ if f.value != 0 and f in self]
        else:
            all_flags = [self]

        return all_flags

    @property
    def is_compound(self) -> bool:
        return self.name is None

    def __str__(self) -> str:
        return ", ".join([f.name for f in self.contents])

    def __repr__(self) -> str:
        flag_names = "|".join([f.name for f in self.contents])
        return f"<{self.__class__.__name__}.{flag_names}>"

    def __format__(self, format_spec: str) -> str:
        if format_spec:
            return super().__format__(format_spec)
        else:
            # use default str if no explicit formatting, otherwise int.__format__ is used which may
            # not be what is expected
            return str(self)


class ResourceMethods(BitFlag):
    GET = auto()
    POST = auto()
    PATCH = auto()
    PUT = auto()
    DELETE = auto()


###


class AlleleAssessmentClassification(StrEnum):
    ONE = "1"
    TWO = "2"
    THREE = "3"
    FOUR = "4"
    FIVE = "5"
    NP = "NP"
    RF = "RF"
    DR = "DR"


class AlleleInterpretationWorkflowStatus(StrEnum):
    INTERPRETATION = "Interpretation"
    REVIEW = "Review"


class AnalysisInterpretationWorkflowStatus(StrEnum):
    NOT_READY = "Not ready"
    INTERPRETATION = "Interpretation"
    REVIEW = "Review"
    MEDICAL_REVIEW = "Medical review"


class CallerTypes(StrEnum):
    CNV = auto()
    SNV = auto()


class Consequence(StrEnum):
    transcript_ablation = auto()
    splice_acceptor_variant = auto()
    splice_donor_variant = auto()
    stop_gained = auto()
    frameshift_variant = auto()
    stop_lost = auto()
    start_lost = auto()
    initiator_codon_variant = auto()
    transcript_amplification = auto()
    inframe_insertion = auto()
    inframe_deletion = auto()
    missense_variant = auto()
    protein_altering_variant = auto()
    splice_region_variant = auto()
    incomplete_terminal_codon_variant = auto()
    start_retained_variant = auto()
    stop_retained_variant = auto()
    synonymous_variant = auto()
    coding_sequence_variant = auto()
    mature_miRNA_variant = auto()
    five_prime_UTR_variant = "5_prime_UTR_variant"
    three_prime_UTR_variant = "3_prime_UTR_variant"
    non_coding_transcript_exon_variant = auto()
    intron_variant = auto()
    NMD_transcript_variant = auto()
    non_coding_transcript_variant = auto()
    upstream_gene_variant = auto()
    downstream_gene_variant = auto()
    TFBS_ablation = auto()
    TFBS_amplification = auto()
    TF_binding_site_variant = auto()
    regulatory_region_ablation = auto()
    regulatory_region_amplification = auto()
    feature_elongation = auto()
    regulatory_region_variant = auto()
    feature_truncation = auto()
    intergenic_variant = auto()


# Used in {analysis,allele}interpretationsnapshot.filtered
class FilteredAlleleCategories(StrEnum):
    CLASSIFICATION = auto()
    CONSEQUENCE = auto()
    FREQUENCY = auto()
    GENE = auto()
    INHERITANCEMODEL = auto()
    POLYPYRIMIDINE = "ppy"
    QUALITY = auto()
    REGION = auto()
    SEGREGATION = auto()


# Used with filter config
class FilterNames(StrEnum):
    CALLERTYPE = auto()  # new
    CLASSIFICATION = auto()
    CONSEQUENCE = auto()
    EXTERNAL = auto()
    FREQUENCY = auto()
    INHERITANCEMODEL = auto()
    PPY = auto()
    QUALITY = auto()
    REGION = auto()
    SEGREGATION = auto()
    SIZE = auto()


class GenomeReference(StrEnum):
    GRCH37 = "GRCh37"
    GRCH38 = "GRCh38"


class GenotypeTypes(StrEnum):
    HOMOZYGOUS = "Homozygous"
    HETEROZYGOUS = "Heterozygous"
    REFERENCE = "Reference"
    NO_COVERAGE = "No coverage"


class InterpretationSnapshotFiltered(StrEnum):
    CLASSIFICATION = "CLASSIFICATION"
    FREQUENCY = "FREQUENCY"
    REGION = "REGION"
    POLYPYRIMIDINE = "POLYPYRIMIDINE"
    GENE = "GENE"
    QUALITY = "QUALITY"
    CONSEQUENCE = "CONSEQUENCE"
    SEGREGATION = "SEGREGATION"
    INHERITANCEMODEL = "INHERITANCEMODEL"


class InterpretationStatus(StrEnum):
    NOT_STARTED = "Not started"
    ONGOING = "Ongoing"
    DONE = "Done"


class SampleSex(StrEnum):
    FEMALE = "Female"
    MALE = "Male"


class SampleType(StrEnum):
    HTS = "HTS"
    SANGER = "Sanger"


class WorkflowTypes(StrEnum):
    ALLELE = auto()
    ANALYSIS = auto()


class YesNo(StrEnum):
    YES = auto()
    NO = auto()


class ReferenceEvalRelevance(StrEnum):
    YES = "Yes"
    NO = "No"
    IGNORE = "Ignore"
    INDIRECTLY = "Indirectly"


class AlleleCategories(StrEnum):
    NOT_STARTED = auto()
    MARKED_REVIEW = auto()
    ONGOING = auto()


class AnalysisCategories(StrEnum):
    NOT_READY = auto()
    NOT_STARTED = auto()
    MARKED_REVIEW = auto()
    MARKED_MEDICALREVIEW = auto()
    ONGOING = auto()


class GenepanelVersion(NamedTuple):
    name: str
    version: str


class AlleleIDGenePanel(NamedTuple):
    allele_id: int
    genepanel: GenepanelVersion


class CustomPredictionCategories(StrEnum):
    dna_conservation = auto()
    domain = auto()
    ortholog_conservation = auto()
    paralog_conservation = auto()
    repeat = auto()
    splice_Effect_manual = "splice_Effect_manual"


class OverviewViews(StrEnum):
    ANALYSES = auto()
    VARIANTS = auto()
    IMPORT = auto()


class SidebarCommentType(StrEnum):
    ANALYSIS = auto()
    EVALUATION = auto()


class AnnotationJobStatus(StrEnum):
    SUBMITTED = "SUBMITTED"
    RUNNING = "RUNNING"
    ANNOTATED = "ANNOTATED"
    CANCELLED = "CANCELLED"
    DONE = "DONE"
    FAILED_SUBMISSION = "FAILED (SUBMISSION)"
    FAILED_ANNOTAION = "FAILED (ANNOTATION)"
    FAILED_DEPOSIT = "FAILED (DEPOSIT)"
    FAILED_PROCESSING = "FAILED (PROCESSING)"


class AnnotationMode(StrEnum):
    ANALYSIS = "Analysis"
    VARIANTS = "Variants"
    SINGLE_VARIANT = "Single variant"


###


K = TypeVar("K")
V = TypeVar("V")
NA = Literal["N/A"]
IntDict = Dict[str, int]
StrDict = Dict[str, str]
FloatDict = Dict[str, float]
Strand = Literal[-1, 1]
StrandSymbol = Literal["-", "+"]
WorkflowStatus = Union[AlleleInterpretationWorkflowStatus, AnalysisInterpretationWorkflowStatus]
