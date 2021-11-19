from __future__ import annotations

from typing import List

from api.schemas.pydantic.v1 import BaseModel, ResourceResponse
from api.schemas.pydantic.v1.alleles import Allele
from api.schemas.pydantic.v1.workflow import AlleleInterpretation


# Creating new resource endpoint models:
#   0. Subclass on ResourceResponse and NOT BaseModel
#   1. Set type on `__root__`
#   2. Set value for `cls.endpoint` (it won't be exported in schema/json)
#   3. If relevant, set `params` with a Dict[str, Any]
#   4. Add new property to ApiModel


class AlleleListResource(ResourceResponse):
    __root__: List[Allele]
    endpoint = "/api/v1/alleles"


class AlleleInterpretationListResource(ResourceResponse):
    __root__: List[AlleleInterpretation]
    endpoint = "/api/v1/workflows/alleles/<int:allele_id>/interpretations/"


###


# Superset of all API endpoint models. Used for dumping JSON schemas / generating typescript
class ApiModel(BaseModel):
    allele_list_resource: AlleleListResource
    allele_interpretation_list_resource: AlleleInterpretationListResource
