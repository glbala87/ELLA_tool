from __future__ import annotations

from typing import List

from api.schemas.pydantic.v1 import BaseModel, ResourceResponse
from api.schemas.pydantic.v1.alleles import Allele
from api.schemas.pydantic.v1.annotations import AnnotationConfig
from api.schemas.pydantic.v1.genepanels import GenepanelFullAssessments
from api.schemas.pydantic.v1.workflow import AlleleInterpretation


# Creating new resource endpoint models:
#   0. Subclass on ResourceResponse and NOT BaseModel
#   1. Subclass or set __root__ on relavent type
#      - If final output is a list, set type on `__root__`
#      - If final output is an obj, include as a parent class
#   2. Set value for `cls.endpoint` (it won't be exported in schema/json)
#   3. If relevant, set `params` with values matching Dict[str, Any]
#   4. Add new property to ApiModel


class AlleleListResource(ResourceResponse):
    __root__: List[Allele]
    endpoints = [
        "/api/v1/alleles",
        "/api/v1/workflows/alleles/<int:allele_id>/interpretations/<int:interpretation_id>/alleles/",
    ]


class AlleleInterpretationListResource(ResourceResponse):
    __root__: List[AlleleInterpretation]
    endpoints = ["/api/v1/workflows/alleles/<int:allele_id>/interpretations/"]


class AlleleGenepanelResource(GenepanelFullAssessments, ResourceResponse):
    endpoints = ["/api/v1/workflows/alleles/<int:allele_id>/genepanels/<gp_name>/<gp_version>/"]


class AnnotationConfigListResource(ResourceResponse):
    __root__: List[AnnotationConfig]
    endpoints = ["/api/v1/annotationconfigs/"]


###


# Superset of all API endpoint models. Used for dumping JSON schemas / generating typescript
class ApiModel(BaseModel):
    allele_list_resource: AlleleListResource
    allele_interpretation_list_resource: AlleleInterpretationListResource
    allele_genepanel_resource: AlleleGenepanelResource
