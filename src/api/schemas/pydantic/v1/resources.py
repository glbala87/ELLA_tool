from __future__ import annotations

import logging
from typing import Dict, List, Optional, Union

from api.schemas.pydantic.v1 import BaseModel, ExtraOK, RequestValidator, ResponseValidator
from api.schemas.pydantic.v1.allele_assessments import (
    AlleleAssessment,
    NewAlleleAssessment,
    ReusedAlleleAssessment,
)
from api.schemas.pydantic.v1.allele_reports import AlleleReport, NewAlleleReport, ReusedAlleleReport
from api.schemas.pydantic.v1.alleles import Allele
from api.schemas.pydantic.v1.annotations import AnnotationConfig
from api.schemas.pydantic.v1.genepanels import Genepanel, GenepanelFullAssessments
from api.schemas.pydantic.v1.interpretationlog import CreateInterpretationLog, InterpretationLog
from api.schemas.pydantic.v1.references import (
    NewReferenceAssessment,
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

WORKFLOWS_ALLELES = "/api/v1/workflows/alleles/<int:allele_id>"
logger = logging.getLogger(__name__)

###
### Response models. Used with @validate_output on API Resources
###

# Creating new resource endpoint models:
#   0. Subclass on ResponseValidator and NOT BaseModel
#   1. Subclass or set __root__ on relavent type
#      - If final output is a list, set type on `__root__`
#      - If final output is an obj, include as a parent class
#   2. Set endpoint string and methods in `cls.endpoints` (used for documentation)
#   4. Add new property to ApiModel


class AlleleListResponse(ResponseValidator):
    __root__: List[Allele]
    endpoints = {
        "/api/v1/alleles": ResourceMethods.GET,
        f"{WORKFLOWS_ALLELES}/interpretations/<int:interpretation_id>/alleles/": ResourceMethods.GET,
    }


class AlleleInterpretationListResponse(ResponseValidator):
    __root__: List[AlleleInterpretation]
    endpoints = {f"{WORKFLOWS_ALLELES}/interpretations/": ResourceMethods.GET}


class AlleleGenepanelResponse(GenepanelFullAssessments, ResponseValidator):
    endpoints = {f"{WORKFLOWS_ALLELES}/genepanels/<gp_name>/<gp_version>/": ResourceMethods.GET}


class AnnotationConfigListResponse(ResponseValidator):
    __root__: List[AnnotationConfig]
    endpoints = {"/api/v1/annotationconfigs/": ResourceMethods.GET}


class AlleleInterpretationLogListResponse(ResponseValidator):
    users: List[User]
    logs: List[InterpretationLog]
    endpoints = {f"{WORKFLOWS_ALLELES}/logs/": ResourceMethods.GET}


class AlleleCollisionResponse(ResponseValidator):
    __root__: List[AlleleCollision]
    endpoints = {f"{WORKFLOWS_ALLELES}/collisions/": ResourceMethods.GET}


class AlleleGenepanelsListResponse(ResponseValidator):
    __root__: List[Genepanel]
    endpoints = {f"{WORKFLOWS_ALLELES}/genepanels/": ResourceMethods.GET}


class AlleleInterpretationResponse(AlleleInterpretation, ResponseValidator):
    endpoints = {
        f"{WORKFLOWS_ALLELES}/interpretations/<int:interpretation_id>/": ResourceMethods.GET
    }


class AlleleInterpretationSnapshotListResponse(ResponseValidator):
    __root__: List[AlleleInterpretationSnapshot]
    endpoints = {f"{WORKFLOWS_ALLELES}/snapshots/": ResourceMethods.GET}


class FinalizeAlleleInterpretationResponse(ResponseValidator):
    allelereport: AlleleReport
    alleleassessment: AlleleAssessment
    referenceassessments: List[ReferenceAssessment]
    endpoints = {f"{WORKFLOWS_ALLELES}/actions/finalizeallele/": ResourceMethods.POST}


class EmptyResponse(ResponseValidator):
    __root__: None
    endpoints = {
        f"{WORKFLOWS_ALLELES}/interpretations/<int:interpretation_id>/": ResourceMethods.PATCH,
        f"{WORKFLOWS_ALLELES}/actions/finalize/": ResourceMethods.POST,
        f"{WORKFLOWS_ALLELES}/interpretations/<int:interpretation_id>/": ResourceMethods.PATCH,
        f"{WORKFLOWS_ALLELES}/actions/override/": ResourceMethods.POST,
        f"{WORKFLOWS_ALLELES}/actions/start/": ResourceMethods.POST,
        f"{WORKFLOWS_ALLELES}/actions/markinterpretation/": ResourceMethods.POST,
        f"{WORKFLOWS_ALLELES}/actions/markreview/": ResourceMethods.POST,
        f"{WORKFLOWS_ALLELES}/actions/reopen/": ResourceMethods.POST,
        f"{WORKFLOWS_ALLELES}/logs/": ResourceMethods.POST,
        f"{WORKFLOWS_ALLELES}/logs/<int:log_id>/": ResourceMethods.PATCH | ResourceMethods.DELETE,
    }

    def json(self, *args, **kwargs) -> str:
        return "null"


###
### Request models. Not used by API (yet), but useful for typescript interfaces
###


class CreateInterpretationLogRequest(CreateInterpretationLog, RequestValidator):
    endpoints = {f"{WORKFLOWS_ALLELES}/logs/": ResourceMethods.POST}


class PatchInterpretationLogRequest(RequestValidator):
    message: str

    endpoints = {f"{WORKFLOWS_ALLELES}/logs/<int:log_id>/": ResourceMethods.PATCH}


class FinalizeAlleleRequest(RequestValidator):
    allele_id: int
    annotation_id: int
    custom_annotation_id: Optional[int]
    alleleassessment: Union[ReusedAlleleAssessment, NewAlleleAssessment]
    referenceassessments: List[Union[ReusedReferenceAssessment, NewReferenceAssessment]]
    allelereport: Union[ReusedAlleleReport, NewAlleleReport]

    endpoints = {f"{WORKFLOWS_ALLELES}/actions/finalizeallele/": ResourceMethods.POST}


class AlleleActionStartRequest(ExtraOK, RequestValidator):
    gp_name: str
    gp_version: str

    endpoints = {f"{WORKFLOWS_ALLELES}/actions/start/": ResourceMethods.POST}


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


class PatchInterpretationRequest(RequestValidator):
    id: Optional[int] = None
    state: Dict
    user_state: Dict

    endpoints = {
        f"{WORKFLOWS_ALLELES}/interpretations/<int:interpretation_id>/": ResourceMethods.PATCH
    }


class AlleleActionFinalizeRequest(MarkInterpretationRequest):
    technical_allele_ids: Optional[List[int]] = None
    notrelevant_allele_ids: Optional[List[int]] = None

    endpoints = {f"{WORKFLOWS_ALLELES}/actions/finalize/": ResourceMethods.POST}


###


# Superset of all API endpoint models. Used for generating JSON schemas / typescript interfaces
class ApiModel(BaseModel):
    allele_list_response: AlleleListResponse
    allele_interpretation_list_response: AlleleInterpretationListResponse
    allele_genepanel_response: AlleleGenepanelResponse
    allele_interpretationlog_list_response: AlleleInterpretationLogListResponse
    allele_collision_response: AlleleCollisionResponse
    allele_genepanels_list_response: AlleleGenepanelsListResponse
    allele_interpretation_response: AlleleInterpretationResponse
    empty_response: EmptyResponse
    allele_interpretation_snapshot_list_response: AlleleInterpretationSnapshotListResponse
    finalize_allele_interpretation_response: FinalizeAlleleInterpretationResponse

    allele_action_finalize_request: AlleleActionFinalizeRequest
    create_interpretation_log_request: CreateInterpretationLogRequest
    patch_interpretation_log_request: PatchInterpretationLogRequest
    finalize_allele_request: FinalizeAlleleRequest
    allele_action_start_request: AlleleActionStartRequest
    mark_interpretation_request: MarkInterpretationRequest
    patch_interpretation_request: PatchInterpretationRequest
