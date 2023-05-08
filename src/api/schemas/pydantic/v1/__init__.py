from __future__ import annotations

import json
from functools import wraps
from logging import getLogger
from typing import (
    Any,
    ClassVar,
    Dict,
    Optional,
    Type,
    Union,
)

import pydantic
from api.config.config import feature_is_enabled
from api.util.types import ResourceMethods
from pydantic.json import pydantic_encoder
from typing_extensions import get_origin

logger = getLogger(__name__)
PydanticBase = pydantic.BaseModel

### Functions


def modify_schema(schema: Dict[str, Any], model: Type[BaseModel]):
    """
    Delete title from schema. This clutters json2ts output by declaring
    every single field as a separate type. Also allow setting arbitrary schema
    values via an overloadable `_meta` class method. ._meta must return a dict which
    is processed as if it were passed to Config.schema_extra.
    NOTE: it is a shallow dict merge and can clobber pydantic generated values
      ref: https://pydantic-docs.helpmanual.io/usage/schema/#schema-customization
    """
    # remove title of fields
    for field_props in schema.get("properties", {}).values():
        field_props.pop("title", None)

    # mark fields with default values as required in schema
    default_fields = set([f.alias for f in model.__fields__.values() if f.default is not None])
    if default_fields:
        schema["required"] = sorted(set(schema.get("required", [])) | default_fields)

    custom_props = model._meta()
    if custom_props:
        schema.update(**custom_props)


# best placed just after @authenticate decorator. If @paginate is used on the resource, set paginated=True
# NOTE: there are only 16 uses of @paginate vs. 101 uses of @authenticate, so defaults to paginated=False
def validate_output(model_cls: Type[ResourceValidator], paginated: bool = False):
    def _validate_output(func):
        @wraps(func)
        def inner(*args, **kwargs):
            # if pydantic validation not enabled, no-op
            if not feature_is_enabled("pydantic"):
                return func(*args, **kwargs)

            if paginated:
                # @paginate returns data in a different structure than otherwise
                result, http_code, headers = func(*args, **kwargs)
            else:
                result = func(*args, **kwargs)

            try:
                ret = model_cls.parse_obj(result)
            except Exception:
                logger.error(
                    f"failed to create {model_cls.__name__} object from {json.dumps(result, default=pydantic_encoder, indent=2)}"
                )
                raise

            if paginated:
                return ret, http_code, headers
            else:
                return ret

        return inner

    return _validate_output


### Classes


class BaseModel(PydanticBase):
    class Config:
        # enable orm_mode so parse_obj can be used with arbitrary classes as well as dicts
        orm_mode = True
        schema_extra = modify_schema
        validate_all = True
        allow_mutation = False
        extra = pydantic.Extra.forbid
        smart_union = True

    def dump(self, **kwargs):
        "serializes to json string, then json.loads back in. optional params sent directly to self.json()"
        return json.loads(self.json(**kwargs))

    @classmethod
    def _meta(cls) -> Optional[Dict[str, Any]]:
        "overload to return custom schema.properties modifications"
        return None


class ExtraOK(BaseModel):
    class Config(BaseModel.Config):
        extra = pydantic.Extra.allow


class ResourceValidator(BaseModel):
    endpoints: ClassVar[Dict[str, ResourceMethods]]

    @classmethod
    def _meta(cls) -> Dict[str, Any]:
        "returns dict used by BaseConfig.schema_extra to customize model schema"
        # keep any doc string description that may already be present
        model_desc = f"{cls.__doc__}\n\n" if cls.__doc__ else ""
        # e.g., POST: /api/v1/alleles
        endpoints_str = "\n".join(f"{v}: {k}" for k, v in cls.endpoints.items())

        return {"description": f"{model_desc}{endpoints_str}"}


class ResponseValidator(ResourceValidator):
    ...


class RequestValidator(ResourceValidator):
    ...
