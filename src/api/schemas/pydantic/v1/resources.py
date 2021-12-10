from __future__ import annotations

import logging
from typing import Any, ClassVar, Dict, List, Optional, Union

from api.schemas.pydantic.v1 import BaseModel, ExtraOK, RequestValidator, ResponseValidator
from api.schemas.pydantic.v1.allele_assessments import (
    AlleleAssessment,
    NewAlleleAssessment,
    ReusedAlleleAssessment,
)
from api.schemas.pydantic.v1.allele_reports import AlleleReport, NewAlleleReport, ReusedAlleleReport
from api.schemas.pydantic.v1.alleles import Allele
from api.schemas.pydantic.v1.annotations import AnnotationConfig
from api.schemas.pydantic.v1.attachment import Attachment
from api.schemas.pydantic.v1.classification import ACMGClassification, ACMGCode
from api.schemas.pydantic.v1.genepanels import Genepanel, GenepanelFullAssessments
from api.schemas.pydantic.v1.interpretationlog import CreateInterpretationLog, InterpretationLog
from api.schemas.pydantic.v1.references import (
    MinimalReferenceAssessment,
    NewReferenceAssessment,
    Reference,
    ReferenceAssessment,
    ReusedReferenceAssessment,
)
from api.schemas.pydantic.v1.users import User
from api.schemas.pydantic.v1.workflow import (
    AlleleCollision,
    AlleleInterpretation,
    AlleleInterpretationSnapshot,
)
from api.util.types import ResourceMethods
from pydantic import Field, root_validator

WORKFLOWS_ALLELES = "/api/v1/workflows/alleles/<int:allele_id>"
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
#   4. Add new property to ApiModel

# Generic responses


class EmptyResponse(ResponseValidator):
    "returns nothing"
    __root__: None

    endpoints = {
        f"{WORKFLOWS_ALLELES}/actions/finalize/": ResourceMethods.POST,
        f"{WORKFLOWS_ALLELES}/actions/markinterpretation/": ResourceMethods.POST,
        f"{WORKFLOWS_ALLELES}/actions/markreview/": ResourceMethods.POST,
        f"{WORKFLOWS_ALLELES}/actions/override/": ResourceMethods.POST,
        f"{WORKFLOWS_ALLELES}/actions/reopen/": ResourceMethods.POST,
        f"{WORKFLOWS_ALLELES}/actions/start/": ResourceMethods.POST,
        f"{WORKFLOWS_ALLELES}/interpretations/<int:interpretation_id>/": ResourceMethods.PATCH,
        f"{WORKFLOWS_ALLELES}/logs/": ResourceMethods.POST,
        f"{WORKFLOWS_ALLELES}/logs/<int:log_id>/": ResourceMethods.PATCH | ResourceMethods.DELETE,
    }

    def json(self, *args, **kwargs) -> str:
        return "null"


class SendFileResponse(ResponseValidator):
    "triggers a file download"

    endpoints = {
        "/api/v1/attachments/analyses/<int:analysis_id>/<int:index>/": ResourceMethods.GET,
        "/api/v1/attachments/upload//api/v1/attachments/<int:attachment_id>": ResourceMethods.GET,
    }


# Specific responses


class ACMGAlleleResponse(ResponseValidator):
    class Config(ExtraOK.Config):
        pass

    __root__: Dict[str, List[ACMGCode]]

    endpoints: ClassVar[Dict] = {"/api/v1/acmg/alleles/": ResourceMethods.POST}


class ACMGClassificationResponse(ACMGClassification, ResponseValidator):
    endpoints = {"/api/v1/acmg/classifications/": ResourceMethods.GET}


class AlleleCollisionResponse(ResponseValidator):
    __root__: List[AlleleCollision]

    endpoints = {f"{WORKFLOWS_ALLELES}/collisions/": ResourceMethods.GET}


class AlleleGenepanelResponse(GenepanelFullAssessments, ResponseValidator):
    endpoints = {f"{WORKFLOWS_ALLELES}/genepanels/<gp_name>/<gp_version>/": ResourceMethods.GET}


class AlleleGenepanelsListResponse(ResponseValidator):
    __root__: List[Genepanel]

    endpoints = {f"{WORKFLOWS_ALLELES}/genepanels/": ResourceMethods.GET}


class AlleleInterpretationListResponse(ResponseValidator):
    __root__: List[AlleleInterpretation]

    endpoints = {f"{WORKFLOWS_ALLELES}/interpretations/": ResourceMethods.GET}


class AlleleInterpretationResponse(AlleleInterpretation, ResponseValidator):
    endpoints = {
        f"{WORKFLOWS_ALLELES}/interpretations/<int:interpretation_id>/": ResourceMethods.GET
    }


class AlleleInterpretationSnapshotListResponse(ResponseValidator):
    __root__: List[AlleleInterpretationSnapshot]

    endpoints = {f"{WORKFLOWS_ALLELES}/snapshots/": ResourceMethods.GET}


class AlleleInterpretationLogListResponse(ResponseValidator):
    users: List[User]
    logs: List[InterpretationLog]

    endpoints = {f"{WORKFLOWS_ALLELES}/logs/": ResourceMethods.GET}


class AlleleListResponse(ResponseValidator):
    __root__: List[Allele]

    endpoints = {
        "/api/v1/alleles": ResourceMethods.GET,
        f"{WORKFLOWS_ALLELES}/interpretations/<int:interpretation_id>/alleles/": ResourceMethods.GET,
    }


class AnnotationConfigListResponse(ResponseValidator):
    __root__: List[AnnotationConfig]

    endpoints = {"/api/v1/annotationconfigs/": ResourceMethods.GET}


class AttachmentListResponse(ResponseValidator):
    __root__: List[Attachment]

    endpoints = {"/api/v1/attachments/": ResourceMethods.GET}


class AttachmentPostResponse(ResponseValidator):
    id: int

    endpoints = {
        "/api/v1/attachments/upload/": ResourceMethods.POST,
        "/api/v1/attachments/<int:attachment_id>": ResourceMethods.POST,
    }


class FinalizeAlleleInterpretationResponse(ResponseValidator):
    allelereport: AlleleReport
    alleleassessment: AlleleAssessment
    referenceassessments: List[ReferenceAssessment]

    endpoints = {f"{WORKFLOWS_ALLELES}/actions/finalizeallele/": ResourceMethods.POST}


class ReferenceListResponse(ResponseValidator):
    __root__: List[Reference]

    endpoints = {"/api/v1/references/": ResourceMethods.GET}


class ReferencePostResponse(Reference, ResponseValidator):
    endpoints = {"/api/v1/references/": ResourceMethods.POST}


class SimilarAllelesResponse(ResponseValidator):
    class Config(ExtraOK.Config):
        pass

    __root__: Dict[str, Allele]

    endpoints = {
        "/api/v1/workflows/similar_alleles/<genepanel_name>/<genepanel_version>/": ResourceMethods.GET
    }


###
### Request models. Used by @request_json to validate JSON sent to the API
###


class ACMGAlleleRequest(RequestValidator):
    allele_ids: List[int]
    gp_name: str
    gp_version: str
    referenceassessments: List[MinimalReferenceAssessment] = Field(default_factory=list)

    endpoints = {"/api/v1/acmg/alleles/": ResourceMethods.POST}


class AlleleActionStartRequest(ExtraOK, RequestValidator):
    gp_name: str
    gp_version: str

    endpoints = {f"{WORKFLOWS_ALLELES}/actions/start/": ResourceMethods.POST}


class CreateInterpretationLogRequest(CreateInterpretationLog, RequestValidator):
    endpoints = {f"{WORKFLOWS_ALLELES}/logs/": ResourceMethods.POST}


class FinalizeAlleleRequest(RequestValidator):
    allele_id: int
    annotation_id: int
    custom_annotation_id: Optional[int]
    alleleassessment: Union[ReusedAlleleAssessment, NewAlleleAssessment]
    referenceassessments: List[Union[ReusedReferenceAssessment, NewReferenceAssessment]]
    allelereport: Union[ReusedAlleleReport, NewAlleleReport]

    endpoints = {f"{WORKFLOWS_ALLELES}/actions/finalizeallele/": ResourceMethods.POST}


class MarkInterpretationRequest(RequestValidator):
    allele_ids: List[int]
    alleleassessment_ids: List[int]
    allelereport_ids: List[int]
    annotation_ids: List[int]
    custom_annotation_ids: List[int]
    excluded_allele_ids: Optional[Dict[str, int]] = None

    endpoints = {
        f"{WORKFLOWS_ALLELES}/actions/markinterpretation/": ResourceMethods.POST,
        f"{WORKFLOWS_ALLELES}/actions/markreview/": ResourceMethods.POST,
    }


class AlleleActionFinalizeRequest(MarkInterpretationRequest):
    technical_allele_ids: Optional[List[int]] = None
    notrelevant_allele_ids: Optional[List[int]] = None

    endpoints = {
        f"{WORKFLOWS_ALLELES}/actions/finalize/": ResourceMethods.POST,
        f"{WORKFLOWS_ALLELES}/snapshots/": ResourceMethods.POST,
    }


class PatchInterpretationLogRequest(RequestValidator):
    message: str

    endpoints = {f"{WORKFLOWS_ALLELES}/logs/<int:log_id>/": ResourceMethods.PATCH}


class PatchInterpretationRequest(RequestValidator):
    id: Optional[int] = None
    state: Dict
    user_state: Dict

    endpoints = {
        f"{WORKFLOWS_ALLELES}/interpretations/<int:interpretation_id>/": ResourceMethods.PATCH
    }


class ReferenceListRequest(RequestValidator):
    pubmedData: Optional[str] = None
    manual: Optional[Dict[str, Any]] = None

    endpoints = {"/api/v1/references/": ResourceMethods.POST}

    @root_validator
    def _xor_keys(cls, values: Dict):
        assert (values.get("manual") is not None) ^ (values.get("pubmedData") is not None)
        return values


###


# Superset of all API endpoint models. Used for generating JSON schemas / typescript interfaces
class ApiModel(BaseModel):
    empty_response: EmptyResponse
    send_file_response: SendFileResponse

    acmg_allele_response: ACMGAlleleResponse
    acmg_classification_response: ACMGClassificationResponse
    allele_collision_response: AlleleCollisionResponse
    allele_genepanel_response: AlleleGenepanelResponse
    allele_genepanels_list_response: AlleleGenepanelsListResponse
    allele_interpretation_list_response: AlleleInterpretationListResponse
    allele_interpretation_response: AlleleInterpretationResponse
    allele_interpretation_snapshot_list_response: AlleleInterpretationSnapshotListResponse
    allele_interpretationlog_list_response: AlleleInterpretationLogListResponse
    allele_list_response: AlleleListResponse
    annotation_config_list_response: AnnotationConfigListResponse
    attachment_list_response: AttachmentListResponse
    attachment_post_response: AttachmentPostResponse
    finalize_allele_interpretation_response: FinalizeAlleleInterpretationResponse
    reference_list_response: ReferenceListResponse
    reference_post_respost: ReferencePostResponse
    similar_alleles_response: SimilarAllelesResponse

    acmg_allele_request: ACMGAlleleRequest
    allele_action_finalize_request: AlleleActionFinalizeRequest
    allele_action_start_request: AlleleActionStartRequest
    create_interpretation_log_request: CreateInterpretationLogRequest
    finalize_allele_request: FinalizeAlleleRequest
    mark_interpretation_request: MarkInterpretationRequest
    patch_interpretation_log_request: PatchInterpretationLogRequest
    patch_interpretation_request: PatchInterpretationRequest
    reference_list_request: ReferenceListRequest
