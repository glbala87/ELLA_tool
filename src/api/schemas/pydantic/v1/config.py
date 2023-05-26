from __future__ import annotations

from typing import Any, Dict, List, Optional, Union

from api.schemas.pydantic.v1 import BaseModel
from api.util.types import (
    AlleleInterpretationWorkflowStatus,
    AnalysisInterpretationWorkflowStatus,
    CustomPredictionCategories,
    OverviewViews,
    SidebarCommentType,
)
from pydantic import Field

# ref: src/api/config/config.schema.json


class AppConfig(BaseModel):
    links_to_clipboard: bool
    non_production_warning: Optional[str]
    annotation_service: str
    attachment_storage: Optional[str]
    max_upload_size: int
    feature_flags: Optional[Dict[str, bool]] = None


class AuthConfig(BaseModel):
    password_expiry_days: int
    password_minimum_length: int
    password_match_groups: List[str]
    password_match_groups_descr: List[str]
    password_num_match_groups: int


class OverviewConfig(BaseModel):
    views: List[OverviewViews]


class AlleleFinalizeRequirementsConfig(BaseModel):
    workflow_status: List[AlleleInterpretationWorkflowStatus]


class AlleleWorkflowConfig(BaseModel):
    finalize_requirements: AlleleFinalizeRequirementsConfig
    can_start: Optional[bool]


class AnalysisFinalizeRequirementsConfig(BaseModel):
    workflow_status: Optional[List[AnalysisInterpretationWorkflowStatus]]
    allow_unclassified: Optional[bool]


class AnalysisWorkflowConfig(BaseModel):
    finalize_requirements: AnalysisFinalizeRequirementsConfig
    can_start: Optional[bool]


class WorkflowsConfig(BaseModel):
    allele: Optional[AlleleWorkflowConfig]
    analysis: Optional[AnalysisWorkflowConfig]


class InterpretationConfig(BaseModel):
    autoIgnoreReferencePubmedIds: List[int]


class CommentTemplates(BaseModel):
    name: str
    template: str
    comment_fields: List[str]


class UserConfig(BaseModel):
    overview: OverviewConfig
    workflows: WorkflowsConfig
    interpretation: InterpretationConfig
    acmg: Optional[Dict[str, Any]]
    deposit: Optional[Dict]
    comment_templates: Optional[List[CommentTemplates]]


class UserConfigMain(BaseModel):
    auth: AuthConfig
    user_config: UserConfig


class UserConfigAuthenticated(UserConfig, UserConfigMain):
    pass


class DisplayConfig(BaseModel):
    field_1: str = Field(..., alias="1")
    field_2: str = Field(..., alias="2")
    field_3: str = Field(..., alias="3")


class PriorityConfig(BaseModel):
    display: DisplayConfig


class FrequencyGroupsConfig(BaseModel):
    external: Dict[str, List[str]]
    internal: Dict[str, List[str]]


class Frequencies(BaseModel):
    groups: FrequencyGroupsConfig


class GeneGroupsConfig(BaseModel):
    MMR: List[str]


class ClassificationOptionConfig(BaseModel):
    name: str
    value: str
    outdated_after_days: Optional[int] = None
    include_report: Optional[bool] = None
    include_analysis_with_findings: Optional[bool] = None
    sort_index: Optional[int] = None


class Classification(BaseModel):
    gene_groups: GeneGroupsConfig
    options: List[ClassificationOptionConfig]


class ReportConfig(BaseModel):
    classification_text: Dict[str, str]


class TranscriptsConfig(BaseModel):
    inclusion_regex: str
    consequences: List[str]


class IgvReferenceConfig(BaseModel):
    fastaURL: str
    cytobandURL: str


class IgvConfig(BaseModel):
    reference: IgvReferenceConfig
    valid_resource_files: List[str]


class ImportConfig(BaseModel):
    automatic_deposit_with_sample_id: bool
    preimport_script: str


class SimilarAllelesConfig(BaseModel):
    max_variants: int
    max_genomic_distance: int


class CommentTypeConfig(BaseModel):
    unclassified: Optional[SidebarCommentType]
    classified: Optional[SidebarCommentType]
    not_relevant: Optional[SidebarCommentType]
    technical: Optional[SidebarCommentType]


class Sidebar(BaseModel):
    columns: List
    classification_options: Dict[str, List[str]]
    comment_type: Optional[CommentTypeConfig]
    shade_multiple_in_gene: bool
    narrow_comment: Optional[bool] = None


class AnalysisInterpretationConfig(BaseModel):
    priority: PriorityConfig
    sidebar: Dict[str, Sidebar]


class CustomAnnotationPredictionConfig(BaseModel):
    key: CustomPredictionCategories
    name: str
    options: List[List[str]]


class CustomAnnotationExternalConfig(BaseModel):
    key: str
    name: str
    only_for_genes: Optional[List[int]]
    url_for_genes: Optional[Dict[str, str]]
    options: Optional[List[List[str]]]
    text: Optional[bool] = None


class CustomAnnotationConfig(BaseModel):
    external: List[CustomAnnotationExternalConfig]
    prediction: List[CustomAnnotationPredictionConfig]


class Formatting(BaseModel):
    operators: Dict[str, str]


class Codes(BaseModel):
    pathogenic: List[str]
    benign: List[str]
    other: List[str]


class Explanation(BaseModel):
    short_criteria: str
    sources: List[str]
    criteria: str
    notes: Optional[str]


class AcmgConfig(BaseModel):
    formatting: Formatting
    codes: Codes
    explanation: Dict[str, Explanation]


class Config(BaseModel):
    app: AppConfig
    user: Union[UserConfigMain, UserConfigAuthenticated]
    analysis: AnalysisInterpretationConfig
    frequencies: Frequencies
    classification: Classification
    report: ReportConfig
    transcripts: TranscriptsConfig
    igv: IgvConfig
    import_: ImportConfig = Field(..., alias="import")
    similar_alleles: SimilarAllelesConfig
    custom_annotation: CustomAnnotationConfig
    acmg: AcmgConfig
