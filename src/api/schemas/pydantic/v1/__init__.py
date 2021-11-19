from __future__ import annotations

import json
from enum import Enum
from functools import wraps
from logging import getLogger
from typing import Any, ClassVar, Dict, Optional, Type, TypeVar

import pydantic
from pydantic.json import pydantic_encoder
from typing_extensions import Literal

### Keep all imports from pydantic in common, so model files always import from here instead
# NOTE: is this dumb? ensures any custom classes/etc. are always used, but may be excessive

logger = getLogger(__name__)

Field = pydantic.Field
PydanticBase = pydantic.BaseModel

### Types

NA = Literal["N/A"]
K = TypeVar("K")
V = TypeVar("V")
IntDict = Dict[str, int]
StrDict = Dict[str, str]
FloatDict = Dict[str, float]

### Enums


class YesNo(str, Enum):
    YES = "yes"
    NO = "no"


class GenomeReference(str, Enum):
    GRCH37 = "GRCh37"
    GRCH38 = "GRCh38"


### Functions


def modify_schema(schema: Dict[str, Any], model: Type[BaseModel]):
    """
    Delete title from schema. This clutters json2ts output by declaring
    every single field as a separate type. Also allow setting arbitrary schema
    values via an overloadable `meta` class method. .meta must return a dict which
    is processed as if it were passed to Config.schema_extra.
    NOTE: it is a shallow dict merge and can clobber pydantic generated values
      ref: https://pydantic-docs.helpmanual.io/usage/schema/#schema-customization
    """
    # remove title of fields
    for field_props in schema.get("properties", {}).values():
        field_props.pop("title", None)

    custom_props = model.meta()
    if custom_props:
        schema.update(**custom_props)


# best placed just after @authenticate decorator and _must_ come before rest_filter
def validate_output(model_cls: Type[ResourceResponse]):
    def _validate_output(func):
        @wraps(func)
        def inner(*args, **kwargs):
            result = func(*args, **kwargs)
            try:
                ret = model_cls.parse_obj(result)
            except pydantic.ValidationError:
                logger.error(
                    f"failed to create {model_cls.__name__} object from {json.dumps(result, default=pydantic_encoder)}"
                )
                raise
            return ret

        return inner

    return _validate_output


### Classes


class BaseModel(PydanticBase):
    class Config:
        schema_extra = modify_schema
        validate_all = True
        allow_mutation = False
        extra = pydantic.Extra.forbid

    @classmethod
    def meta(cls) -> Optional[Dict[str, Any]]:
        "overload to return custom schema.properties modifications"
        return None


class ExtraOK(BaseModel):
    class Config(BaseModel.Config):
        extra = pydantic.Extra.allow


class ResourceResponse(BaseModel):
    endpoint: ClassVar[str] = "Generic Endpoint"
    params: ClassVar[Optional[Dict[str, Any]]] = None

    @classmethod
    def meta(cls) -> Dict[str, Any]:
        "returns dict used by BaseConfig.schema_extra to customize model schema"
        desc = cls.endpoint
        if cls.params:
            param_str = "&".join([f"{k}={v}" for k, v in cls.params.items()])
            desc += f"?{param_str}"
        return {"description": desc}
