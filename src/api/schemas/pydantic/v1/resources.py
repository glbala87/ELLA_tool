from __future__ import annotations

import logging
from typing import Any, ClassVar, Dict, List, Optional, Union

from pydantic import Field, create_model, root_validator

from api.schemas.pydantic.v1 import BaseModel, ExtraOK, RequestValidator, ResponseValidator
from api.schemas.pydantic.v1.allele_assessments import (
    AlleleAssessment,
    NewAlleleAssessment,
    ReusedAlleleAssessment,
)
from api.schemas.pydantic.v1.allele_reports import AlleleReport, NewAlleleReport, ReusedAlleleReport
from api.schemas.pydantic.v1.alleles import Allele, AlleleGene, AlleleOverview
from api.schemas.pydantic.v1.analyses import Analysis, AnalysisStats, OverviewAnalysis
from api.schemas.pydantic.v1.annotations import (
    AnnotationConfig,
    AnnotationJob,
    AnnotationSample,
    CreateAnnotationJob,
    CustomAnnotation,
)
from api.schemas.pydantic.v1.attachment import Attachment
from api.schemas.pydantic.v1.broadcast import Broadcast
from api.schemas.pydantic.v1.classification import ACMGClassification, ACMGCodeList
from api.schemas.pydantic.v1.common import Comment
from api.schemas.pydantic.v1.config import Config
from api.schemas.pydantic.v1.filterconfig import FilterConfig

# from api.schemas.pydantic.v1.gene_assessments import GeneAssessment
from api.schemas.pydantic.v1.genepanels import (
    GeneAssessment,
    Genepanel,
    GenepanelFullAssessmentsInheritances,
    GenepanelSingle,
    GenepanelStats,
    NewGenepanelGene,
)
from api.schemas.pydantic.v1.igv import TrackConfig
from api.schemas.pydantic.v1.interpretationlog import CreateInterpretationLog, InterpretationLog
from api.schemas.pydantic.v1.references import (
    NewReferenceAssessment,
    OptReferenceAssessment,
    Reference,
    ReferenceAssessment,
    ReusedReferenceAssessment,
)
from api.schemas.pydantic.v1.search import SearchOptions, SearchResults
from api.schemas.pydantic.v1.users import OverviewUserStats, User, UserFull
from api.schemas.pydantic.v1.workflow import (
    AlleleCollision,
    AlleleInterpretation,
    AlleleInterpretationSnapshot,
    AnalysisInterpretation,
    AnalysisInterpretationSnapshot,
)
from api.util.types import CallerTypes, ResourceMethods
from api.util.util import from_camel

WORKFLOWS_ALLELES = "/api/v1/workflows/alleles/<int:allele_id>"
WORKFLOWS_ANALYSES = "/api/v1/workflows/analyses/<int:analysis_id>"
logger = logging.getLogger(__name__)

###
### Response models. Used with @validate_output on API Resources
###

# Creating new resource endpoint models:
#   0. Subclass on ResponseValidator and NOT BaseModel
#   1. Subclass or set __root__ on relavent type
#      - If final output is a list/dict, set type on `__root__`
#         - NB: if using Dict, you must also set Config.extra = Extra.ignore
#             ref: https://github.com/samuelcolvin/pydantic/issues/3505
#      - If final output is an obj, include as a parent class
#   2. Set endpoint string and methods in `cls.endpoints` (used for documentation)

# Generic responses


class EmptyResponse(ResponseValidator):
    "returns nothing"
    __root__: None

    endpoints = {
        "/api/v1/genepanels/": ResourceMethods.POST,
        "/api/v1/import/service/jobs/<int:id>/": ResourceMethods.DELETE,
        "/api/v1/ui/exceptionlog/": ResourceMethods.POST,
        "/api/v1/users/actions/changepassword/": ResourceMethods.POST,
        "/api/v1/users/actions/logout/": ResourceMethods.POST,
        f"{WORKFLOWS_ALLELES}/actions/finalize/": ResourceMethods.POST,
        f"{WORKFLOWS_ALLELES}/actions/markinterpretation/": ResourceMethods.POST,
        f"{WORKFLOWS_ALLELES}/actions/markreview/": ResourceMethods.POST,
        f"{WORKFLOWS_ALLELES}/actions/override/": ResourceMethods.POST,
        f"{WORKFLOWS_ALLELES}/actions/reopen/": ResourceMethods.POST,
        f"{WORKFLOWS_ALLELES}/actions/start/": ResourceMethods.POST,
        f"{WORKFLOWS_ALLELES}/interpretations/<int:interpretation_id>/": ResourceMethods.PATCH,
        f"{WORKFLOWS_ALLELES}/logs/": ResourceMethods.POST,
        f"{WORKFLOWS_ALLELES}/logs/<int:log_id>/": ResourceMethods.PATCH | ResourceMethods.DELETE,
        f"{WORKFLOWS_ALLELES}/snapshots/": ResourceMethods.POST,
        f"{WORKFLOWS_ANALYSES}/actions/finalize/": ResourceMethods.POST,
        f"{WORKFLOWS_ANALYSES}/actions/markinterpretation/": ResourceMethods.POST,
        f"{WORKFLOWS_ANALYSES}/actions/markmedicalreview/": ResourceMethods.POST,
        f"{WORKFLOWS_ANALYSES}/actions/marknotready/": ResourceMethods.POST,
        f"{WORKFLOWS_ANALYSES}/actions/markreview/": ResourceMethods.POST,
        f"{WORKFLOWS_ANALYSES}/actions/override/": ResourceMethods.POST,
        f"{WORKFLOWS_ANALYSES}/actions/reopen/": ResourceMethods.POST,
        f"{WORKFLOWS_ANALYSES}/actions/start/": ResourceMethods.POST,
        f"{WORKFLOWS_ANALYSES}/interpretations/<int:interpretation_id>/": ResourceMethods.PATCH,
        f"{WORKFLOWS_ANALYSES}/interpretations/<int:interpretation_id>/finishallowed": ResourceMethods.GET,
        f"{WORKFLOWS_ANALYSES}/logs/": ResourceMethods.POST,
        f"{WORKFLOWS_ANALYSES}/logs/<int:log_id>/": ResourceMethods.PATCH | ResourceMethods.DELETE,
        f"{WORKFLOWS_ANALYSES}/snapshots/": ResourceMethods.POST,
    }

    def json(self, *args, **kwargs) -> str:
        return "null"


class SendFileResponse(EmptyResponse):
    "triggers a file download"

    endpoints = {
        "/api/v1/attachments/<int:attachment_id>": ResourceMethods.GET,
        "/api/v1/attachments/analyses/<int:analysis_id>/<int:index>/": ResourceMethods.GET,
        "/api/v1/attachments/upload/": ResourceMethods.GET,
        "/api/v1/igv/<filename>": ResourceMethods.GET,
        "/api/v1/igv/tracks/analyses/<int:analysis_id>/<filename>": ResourceMethods.GET,
        "/api/v1/igv/tracks/dynamic/classifications/": ResourceMethods.GET,
        "/api/v1/igv/tracks/dynamic/genepanel/<gp_name>/<gp_version>/": ResourceMethods.GET,
        "/api/v1/igv/tracks/dynamic/regions_of_interest/<int:analysis_id>/": ResourceMethods.GET,
        "/api/v1/igv/tracks/dynamic/variants/<int:analysis_id>/": ResourceMethods.GET,
        "/api/v1/igv/tracks/static/<filepath>": ResourceMethods.GET,
        "/api/v1/users/actions/login/": ResourceMethods.POST,
        "/static/<path:filename>": ResourceMethods.GET,
    }


class UnvalidatedResponse(ExtraOK, ResponseValidator):
    """Placeholder for endpoints with responses we don't care about / don't validate"""

    endpoints = {
        "/api/v1/docs/": ResourceMethods.GET,
        "/api/v1/docs/<path:path>": ResourceMethods.GET,
        "/api/v1/docs/dist/<path:filename>": ResourceMethods.GET,
        "/api/v1/specs/": ResourceMethods.GET,
    }


# Specific responses


class ACMGAlleleResponse(ResponseValidator):
    class Config(ExtraOK.Config):
        pass

    __root__: Dict[str, ACMGCodeList]

    endpoints: ClassVar[Dict] = {"/api/v1/acmg/alleles/": ResourceMethods.POST}


class ACMGClassificationResponse(ACMGClassification, ResponseValidator):
    endpoints = {"/api/v1/acmg/classifications/": ResourceMethods.GET}


class AlleleAssessmentResponse(AlleleAssessment, ResponseValidator):
    endpoints = {"/api/v1/alleleassessments/<int:aa_id>/": ResourceMethods.GET}


class AlleleAssessmentListResponse(ResponseValidator):
    __root__: List[AlleleAssessment]

    endpoints = {"/api/v1/alleleassessments/": ResourceMethods.GET}


class AlleleCollisionResponse(ResponseValidator):
    __root__: List[AlleleCollision]

    endpoints = {
        f"{WORKFLOWS_ALLELES}/collisions/": ResourceMethods.GET,
        f"{WORKFLOWS_ANALYSES}/collisions/": ResourceMethods.GET,
    }


class AlleleGeneListResponse(ResponseValidator):
    __root__: List[AlleleGene]

    endpoints = {"/api/v1/alleles/by-gene/": ResourceMethods.GET}


class AlleleGenepanelResponse(GenepanelFullAssessmentsInheritances, ResponseValidator):
    endpoints = {
        f"{WORKFLOWS_ALLELES}/genepanels/<gp_name>/<gp_version>/": ResourceMethods.GET,
        f"{WORKFLOWS_ANALYSES}/genepanels/<gp_name>/<gp_version>/": ResourceMethods.GET,
    }


class AlleleInterpretationListResponse(ResponseValidator):
    __root__: List[AlleleInterpretation]

    endpoints = {f"{WORKFLOWS_ALLELES}/interpretations/": ResourceMethods.GET}


class AlleleInterpretationResponse(AlleleInterpretation, ResponseValidator):
    endpoints = {
        f"{WORKFLOWS_ALLELES}/interpretations/<int:interpretation_id>/": ResourceMethods.GET
    }


class AlleleInterpretationSnapshotListResponse(ResponseValidator):
    __root__: List[AlleleInterpretationSnapshot]

    endpoints = {
        f"{WORKFLOWS_ALLELES}/snapshots/": ResourceMethods.GET,
        f"{WORKFLOWS_ALLELES}/actions/finalize/": ResourceMethods.GET,
    }


class InterpretationLogListResponse(ResponseValidator):
    users: List[User]
    logs: List[InterpretationLog]

    endpoints = {
        f"{WORKFLOWS_ALLELES}/logs/": ResourceMethods.GET,
        f"{WORKFLOWS_ANALYSES}/logs/": ResourceMethods.GET,
    }


class AlleleListResponse(ResponseValidator):
    __root__: List[Allele]

    endpoints = {
        "/api/v1/alleles/": ResourceMethods.GET,
        f"{WORKFLOWS_ALLELES}/interpretations/<int:interpretation_id>/alleles/": ResourceMethods.GET,
        f"{WORKFLOWS_ANALYSES}/interpretations/<int:interpretation_id>/alleles/": ResourceMethods.GET,
    }


class AlleleReportResponse(AlleleReport, ResponseValidator):
    endpoints = {"/api/v1/allelereports/<int:ar_id>/": ResourceMethods.GET}


class AlleleReportListResponse(ResponseValidator):
    __root__: List[AlleleReport]

    endpoints = {"/api/v1/allelereports/": ResourceMethods.GET}


class AnalysisResponse(Analysis, ResponseValidator):
    endpoints = {"/api/v1/analyses/<int:analysis_id>/": ResourceMethods.GET}


class AnalysisInterpretationResponse(AnalysisInterpretation, ResponseValidator):
    endpoints = {
        f"{WORKFLOWS_ANALYSES}/interpretations/<int:interpretation_id>/": ResourceMethods.GET
    }


class AnalysisInterpretationListResponse(ResponseValidator):
    __root__: List[AnalysisInterpretation]

    endpoints = {f"{WORKFLOWS_ANALYSES}/interpretations/": ResourceMethods.GET}


class AnalysisInterpretationSnapshotListResponse(ResponseValidator):
    __root__: List[AnalysisInterpretationSnapshot]

    endpoints = {
        f"{WORKFLOWS_ANALYSES}/actions/finalize/": ResourceMethods.GET,
        f"{WORKFLOWS_ANALYSES}/snapshots/": ResourceMethods.GET,
    }


class AnalysisListResponse(ResponseValidator):
    __root__: List[Analysis]

    endpoints = {
        "/api/v1/alleles/<int:allele_id>/analyses/": ResourceMethods.GET,
        "/api/v1/analyses/": ResourceMethods.GET,
    }


class AnalysisStatsResponse(AnalysisStats, ResponseValidator):
    endpoints = {f"{WORKFLOWS_ANALYSES}/stats/": ResourceMethods.GET}


class AnnotationConfigListResponse(ResponseValidator):
    __root__: List[AnnotationConfig]

    endpoints = {"/api/v1/annotationconfigs/": ResourceMethods.GET}


class AnnotationJobResponse(AnnotationJob, ResponseValidator):
    endpoints = {
        "/api/v1/import/service/jobs/": ResourceMethods.POST,
        "/api/v1/import/service/jobs/<int:id>/": ResourceMethods.PATCH,
    }


class AnnotationJobListResponse(ResponseValidator):
    __root__: List[AnnotationJob]

    endpoints = {"/api/v1/import/service/jobs/": ResourceMethods.GET}


class AnnotationSampleListResponse(ResponseValidator):
    __root__: List[AnnotationSample]

    endpoints = {"/api/v1/import/service/samples/": ResourceMethods.GET}


class AnnotationServiceStatusResponse(ResponseValidator):
    running: bool

    endpoints = {"/api/v1/import/service/running/": ResourceMethods.GET}


class AttachmentListResponse(ResponseValidator):
    __root__: List[Attachment]

    endpoints = {"/api/v1/attachments/": ResourceMethods.GET}


class AttachmentPostResponse(ResponseValidator):
    id: int

    endpoints = {
        "/api/v1/attachments/<int:attachment_id>": ResourceMethods.POST,
        "/api/v1/attachments/upload/": ResourceMethods.POST,
    }


class BroadcastResponse(ResponseValidator):
    __root__: List[Broadcast]

    endpoints = {"/api/v1/broadcasts/": ResourceMethods.GET}


class ConfigResponse(Config, ResponseValidator):
    endpoints = {"/api/v1/config/": ResourceMethods.GET}


class CustomAnnotationResponse(CustomAnnotation, ResponseValidator):
    endpoints = {"/api/v1/customannotations/": ResourceMethods.POST}


class CustomAnnotationListResponse(ResponseValidator):
    __root__: List[CustomAnnotation]

    endpoints = {"/api/v1/customannotations/": ResourceMethods.GET}


class FilteredAllelesResponse(ResponseValidator):
    allele_ids: List[int]
    excluded_alleles_by_caller_type: Dict[CallerTypes, Dict[str, List[int]]]

    endpoints = {
        f"{WORKFLOWS_ANALYSES}/interpretations/<int:interpretation_id>/filteredalleles/": ResourceMethods.GET
    }


class FilterConfigResponse(FilterConfig, ResponseValidator):
    endpoints = {"/api/v1/filterconfigs/<int:filterconfig_id>": ResourceMethods.GET}


class FilterConfigListResponse(ResponseValidator):
    __root__: List[FilterConfig]

    endpoints = {f"{WORKFLOWS_ANALYSES}/filterconfigs/": ResourceMethods.GET}


class FinalizeAlleleInterpretationResponse(ResponseValidator):
    allelereport: AlleleReport
    alleleassessment: AlleleAssessment
    referenceassessments: List[ReferenceAssessment]

    endpoints = {
        f"{WORKFLOWS_ALLELES}/actions/finalizeallele/": ResourceMethods.POST,
        f"{WORKFLOWS_ANALYSES}/actions/finalizeallele/": ResourceMethods.POST,
    }


class GeneAssessmentResponse(GeneAssessment, ResponseValidator):
    endpoints = {"/api/v1/geneassessments/": ResourceMethods.POST}


class GeneAssessmentListResponse(ResponseValidator):
    __root__: List[GeneAssessment]

    endpoints = {"/api/v1/geneassessments/": ResourceMethods.GET}


class GenePanelListResponse(ResponseValidator):
    __root__: List[Genepanel]

    endpoints = {
        "/api/v1/genepanels/": ResourceMethods.GET,
        f"{WORKFLOWS_ALLELES}/genepanels/": ResourceMethods.GET,
    }


class GenePanelResponse(GenepanelSingle, ResponseValidator):
    endpoints = {"/api/v1/genepanels/<name>/<version>/": ResourceMethods.GET}


class GenePanelStatsResponse(ResponseValidator):
    overlap: List[GenepanelStats]

    endpoints = {"/api/v1/genepanels/<name>/<version>/stats/": ResourceMethods.GET}


class OverviewAlleleResponse(ResponseValidator):
    not_started: List[AlleleOverview]
    ongoing: List[AlleleOverview]
    marked_review: List[AlleleOverview]

    endpoints = {"/api/v1/igv/search/": ResourceMethods.GET}


class IgvTrackConfigListResponse(ResponseValidator):
    class Config(ExtraOK.Config):
        pass

    __root__: Dict[str, TrackConfig]

    endpoints = {"/api/v1/igv/tracks/<int:analysis_id>/": ResourceMethods.GET}


class OverviewAlleleFinalizedResponse(ResponseValidator):
    class Config(ExtraOK.Config):
        pass

    __root__: List[AlleleOverview]

    endpoints = {"/api/v1/overviews/alleles/finalized/": ResourceMethods.GET}


class OverviewAnalysisResponse(ResponseValidator):
    not_ready: List[OverviewAnalysis]
    not_started: List[OverviewAnalysis]
    marked_review: List[OverviewAnalysis]
    marked_medicalreview: List[OverviewAnalysis]
    ongoing: List[OverviewAnalysis]

    endpoints = {"/api/v1/overviews/analyses/": ResourceMethods.GET}


class OverviewAnalysisFinalizedResponse(ResponseValidator):
    __root__: List[OverviewAnalysis]

    endpoints = {"/api/v1/overviews/analyses/finalized/": ResourceMethods.GET}


class ReferenceAssessmentResponse(ReferenceAssessment, ResponseValidator):
    endpoints = {
        "/api/v1/referenceassessments/": ResourceMethods.POST,
        "/api/v1/referenceassessments/<int:ra_id>/": ResourceMethods.GET,
    }


class ReferenceAssessmentListResponse(ResponseValidator):
    __root__: List[ReferenceAssessment]

    endpoints = {"/api/v1/referenceassessments/": ResourceMethods.GET}


class ReferenceListResponse(ResponseValidator):
    __root__: List[Reference]

    endpoints = {"/api/v1/references/": ResourceMethods.GET}


class ReferencePostResponse(Reference, ResponseValidator):
    endpoints = {"/api/v1/references/": ResourceMethods.POST}


class SearchOptionsResponse(SearchOptions, ResponseValidator):
    endpoints = {"/api/v1/search/options/": ResourceMethods.GET}


class SearchResponse(SearchResults, ResponseValidator):
    endpoints = {"/api/v1/search/": ResourceMethods.GET}


class SimilarAllelesResponse(ResponseValidator):
    class Config(ExtraOK.Config):
        pass

    __root__: Dict[str, List[Allele]]

    endpoints = {
        "/api/v1/workflows/similar_alleles/<genepanel_name>/<genepanel_version>/": ResourceMethods.GET
    }


class UserListResponse(ResponseValidator):
    __root__: List[UserFull]

    endpoints = {"/api/v1/users/": ResourceMethods.GET}


class UserResponse(ResponseValidator, UserFull):
    endpoints = {
        "/api/v1/users/<int:user_id>/": ResourceMethods.GET,
        "/api/v1/users/currentuser/": ResourceMethods.GET,
    }


class UserStatsResponse(OverviewUserStats, ResponseValidator):
    endpoints = {"/api/v1/overviews/userstats/": ResourceMethods.GET}


###
### Request models. Used by @request_json to validate JSON sent to the API
###


class EmptyRequest(RequestValidator):
    "returns nothing"

    def json(self, *args, **kwargs) -> str:
        return "null"

    __root__: None

    endpoints = {
        "/api/v1/attachments/<int:attachment_id>": ResourceMethods.POST,
        "/api/v1/attachments/upload/": ResourceMethods.POST,
        "/api/v1/users/actions/logout/": ResourceMethods.POST,
        f"{WORKFLOWS_ALLELES}/actions/override/": ResourceMethods.POST,
        f"{WORKFLOWS_ALLELES}/actions/reopen/": ResourceMethods.POST,
        f"{WORKFLOWS_ANALYSES}/actions/override/": ResourceMethods.POST,
        f"{WORKFLOWS_ANALYSES}/actions/reopen/": ResourceMethods.POST,
        f"{WORKFLOWS_ANALYSES}/actions/start/": ResourceMethods.POST,
    }


class MarkAlleleInterpretationRequest(RequestValidator):
    allele_ids: List[int]
    alleleassessment_ids: List[int]
    allelereport_ids: List[int]
    annotation_ids: List[int]
    custom_annotation_ids: List[int]
    # NOTE/HACK: excluded_allele_ids should only appear on MarkAnalysisInt..., but the existing python tests send it along anyway
    # Including here as an Optional so tests pass. To be corrected in backend refactor. Someday.
    excluded_allele_ids: Optional[Dict[str, List[int]]]

    endpoints = {
        f"{WORKFLOWS_ALLELES}/actions/markinterpretation/": ResourceMethods.POST,
        f"{WORKFLOWS_ALLELES}/actions/markreview/": ResourceMethods.POST,
        f"{WORKFLOWS_ALLELES}/actions/finalize/": ResourceMethods.POST,
        f"{WORKFLOWS_ALLELES}/snapshots/": ResourceMethods.POST,
    }


class ACMGAlleleRequest(RequestValidator):
    allele_ids: List[int]
    gp_name: str
    gp_version: str
    referenceassessments: List[OptReferenceAssessment] = Field(default_factory=list)

    endpoints = {"/api/v1/acmg/alleles/": ResourceMethods.POST}


class AlleleActionStartRequest(ExtraOK, RequestValidator):
    gp_name: str
    gp_version: str

    endpoints = {f"{WORKFLOWS_ALLELES}/actions/start/": ResourceMethods.POST}


class CreateExceptionLogRequest(RequestValidator):
    message: str
    location: str
    stacktrace: str
    state: Dict = Field(default_factory=dict)

    endpoints = {"/api/v1/ui/exceptionlog/": ResourceMethods.POST}


class CreateAnnotationJobRequest(CreateAnnotationJob, RequestValidator):
    endpoints = {"/api/v1/import/service/jobs/": ResourceMethods.POST}


class MarkAnalysisInterpretationRequest(MarkAlleleInterpretationRequest):
    excluded_allele_ids: Dict[str, List[int]]
    technical_allele_ids: List[int] = Field(default_factory=list)
    notrelevant_allele_ids: List[int] = Field(default_factory=list)

    endpoints = {
        f"{WORKFLOWS_ANALYSES}/actions/finalize/": ResourceMethods.POST,
        f"{WORKFLOWS_ANALYSES}/actions/markmedicalreview/": ResourceMethods.POST,
        f"{WORKFLOWS_ANALYSES}/actions/markreview/": ResourceMethods.POST,
        f"{WORKFLOWS_ANALYSES}/snapshots/": ResourceMethods.POST,
        f"{WORKFLOWS_ANALYSES}/actions/markinterpretation/": ResourceMethods.POST,
        f"{WORKFLOWS_ANALYSES}/actions/marknotready/": ResourceMethods.POST,
    }


class CreateInterpretationLogRequest(CreateInterpretationLog, RequestValidator):
    endpoints = {
        f"{WORKFLOWS_ALLELES}/logs/": ResourceMethods.POST,
        f"{WORKFLOWS_ANALYSES}/logs/": ResourceMethods.POST,
    }


class FinalizeAlleleRequest(RequestValidator):
    allele_id: int
    annotation_id: int
    custom_annotation_id: Optional[int]
    alleleassessment: Union[ReusedAlleleAssessment, NewAlleleAssessment]
    referenceassessments: List[Union[ReusedReferenceAssessment, NewReferenceAssessment]]
    allelereport: Union[ReusedAlleleReport, NewAlleleReport]

    endpoints = {
        f"{WORKFLOWS_ALLELES}/actions/finalizeallele/": ResourceMethods.POST,
        f"{WORKFLOWS_ANALYSES}/actions/finalizeallele/": ResourceMethods.POST,
    }


class GeneAssessmentPostRequest(RequestValidator):
    gene_id: int
    genepanel_name: str
    genepanel_version: str
    analysis_id: Optional[int] = None
    evaluation: Comment
    presented_geneassessment_id: Optional[int] = None

    endpoints = {"/api/v1/geneassessments/": ResourceMethods.POST}


class PatchInterpretationLogRequest(RequestValidator):
    message: str

    endpoints = {
        f"{WORKFLOWS_ALLELES}/logs/<int:log_id>/": ResourceMethods.PATCH,
        f"{WORKFLOWS_ANALYSES}/logs/<int:log_id>/": ResourceMethods.PATCH,
    }


class PatchInterpretationRequest(RequestValidator):
    id: Optional[int] = None
    state: Dict
    user_state: Dict

    endpoints = {
        f"{WORKFLOWS_ALLELES}/interpretations/<int:interpretation_id>/": ResourceMethods.PATCH,
        f"{WORKFLOWS_ANALYSES}/interpretations/<int:interpretation_id>/": ResourceMethods.PATCH,
    }


class PatchAnnotationJobRequest(RequestValidator):
    status: Optional[str]
    message: Optional[str]
    task_id: Optional[str]

    endpoints = {
        "/api/v1/import/service/jobs/<int:id>/": ResourceMethods.PATCH,
    }


class ReferenceAssessmentPostRequest(RequestValidator):
    id: Optional[int] = None
    allele_id: int
    reference_id: int
    evaluation: Dict
    analysis_id: Optional[int] = None
    genepanel_name: str
    genepanel_version: str

    endpoints = {"/api/v1/referenceassessments/": ResourceMethods.POST}


class ReferenceListRequest(RequestValidator):
    pubmedData: Optional[str] = None
    manual: Optional[Dict[str, Any]] = None

    endpoints = {"/api/v1/references/": ResourceMethods.POST}

    @root_validator
    def _xor_keys(cls, values: Dict):
        assert (values.get("manual") is not None) ^ (values.get("pubmedData") is not None)
        return values


class LoginRequest(RequestValidator):
    username: str
    password: str

    endpoints = {"/api/v1/users/actions/login/": ResourceMethods.POST}


class ChangePasswordRequest(RequestValidator):
    username: str
    password: str
    new_password: str

    endpoints = {"/api/v1/users/actions/changepassword/": ResourceMethods.POST}


class CreateGenepanelRequest(RequestValidator):
    name: str
    version: str
    genes: List[NewGenepanelGene]
    usergroups: List[int]

    endpoints = {"/api/v1/genepanels/": ResourceMethods.POST}


class CreateCustomAnnotationRequest(RequestValidator):
    allele_id: int
    annotations: Dict  # TODO: where is this defined?
    user_id: Optional[int]

    endpoints = {"/api/v1/customannotations/": ResourceMethods.POST}


###


def gen_api_model():
    import api.schemas.pydantic.v1.resources as pr

    model_kwargs = {}
    for validator_name in [k for k in dir(pr) if k.endswith("Response") or k.endswith("Request")]:
        model_kwargs[from_camel(validator_name)] = (getattr(pr, validator_name), ...)

    return create_model("ApiModel", __base__=BaseModel, **model_kwargs)
