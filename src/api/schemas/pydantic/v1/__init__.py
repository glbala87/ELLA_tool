from __future__ import annotations

import json
from functools import wraps
from logging import getLogger
from typing import Any, ClassVar, Dict, Optional, Type, Union

import pydantic
from api.config.config import feature_is_enabled
from api.util.types import ResourceMethods
from pydantic.json import pydantic_encoder
from typing_extensions import get_origin

### Keep all imports from pydantic in common, so model files always import from here instead
# NOTE: is this dumb? ensures any custom classes/etc. are always used, but may be excessive

logger = getLogger(__name__)

Field = pydantic.Field
PydanticBase = pydantic.BaseModel


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
            except pydantic.ValidationError:
                logger.error(
                    f"failed to create {model_cls.__name__} object from {json.dumps(result, default=pydantic_encoder)}"
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
        schema_extra = modify_schema
        validate_all = True
        allow_mutation = False
        extra = pydantic.Extra.forbid

    def dump(self, **kwargs):
        "serializes to json string, then json.loads back in. optional params sent directly to self.json()"
        return json.loads(self.json(**kwargs))

    @classmethod
    def meta(cls) -> Optional[Dict[str, Any]]:
        "overload to return custom schema.properties modifications"
        return None

    # Pydantic gets easily confused identifying the "correct" BaseModel to use from a Union.
    # Here, we try/except to find a class that validates without error. This is pretty hacky, but
    # necessary with the current API structure re-using the same keys with different formats.
    @pydantic.root_validator(pre=True)
    def _validate_unions(cls, values: Dict):
        # look for any fields with types Union[BaseModel, ...]
        for field in cls.__fields__.values():
            if values.get(field.name) is not None and get_origin(field.type_) is Union:
                if not field.sub_fields:
                    logger.warning(
                        f"{cls.__name__}.{field.name} is Union, but has no sub_fields. Huh?"  # type: ignore
                    )
                    continue

                is_seq = False
                sub_fields = field.sub_fields
                if len(field.sub_fields) == 1 and field.sub_fields[0].sub_fields:
                    # e.g., List[Union[TypeA, TypeB]]
                    is_seq = True
                    sub_fields = field.sub_fields[0].sub_fields

                # only attempt if all Union-ed types are BaseModel subtypes
                field_types = [f.type_ for f in sub_fields if issubclass(f.type_, BaseModel)]
                if len(field_types) == len(sub_fields):
                    new_val = None
                    errs = {}
                    for ft in field_types:
                        try:
                            if is_seq:
                                new_val = [ft.parse_obj(i) for i in values[field.name]]
                            else:
                                new_val = ft.parse_obj(values[field.name])  # type: ignore
                            break
                        except pydantic.ValidationError as e:
                            errs[ft.__name__] = str(e)

                    if new_val:
                        values[field.name] = new_val
                    elif len(errs) == len(field_types):
                        raise ValueError(
                            f"{field.name} failed all validation attempts\n"
                            + "\n".join(f"{k}: {v}" for k, v in errs.items())
                            + "\n"
                        )

        return values


class ExtraOK(BaseModel):
    class Config(BaseModel.Config):
        extra = pydantic.Extra.allow


class ResourceValidator(BaseModel):
    endpoints: ClassVar[Dict[str, ResourceMethods]]

    @classmethod
    def meta(cls) -> Dict[str, Any]:
        "returns dict used by BaseConfig.schema_extra to customize model schema"
        return {"description": "\n".join(f"{v}: {k}" for k, v in cls.endpoints.items())}


class ResponseValidator(ResourceValidator):
    ...


class RequestValidator(ResourceValidator):
    ...


class Comment(BaseModel):
    comment: str
