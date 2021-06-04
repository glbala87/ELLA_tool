import logging
from dataclasses import dataclass
from typing import Mapping

from vardb.deposit.annotationconverters.annotationconverter import (
    AnnotationConverter,
    ConverterArgs,
    Primitives,
    TypeConverter,
)

log = logging.getLogger(__name__)


class MappingConverter(AnnotationConverter):
    config: "Config"

    @dataclass(frozen=True)
    class Config(AnnotationConverter.Config):
        item_separator: str = ","
        keyvalue_separator: str = ":"
        target_type: str = "string"
        target_type_throw: bool = True

    def __call__(self, args: ConverterArgs) -> Mapping[str, Primitives]:
        assert isinstance(
            args.value, str
        ), f"Invalid parameter for MappingConverter: {args.value} ({type(args.value)})"

        data = {}
        converter = TypeConverter[self.config.target_type]
        for kv in args.value.split(self.config.item_separator):
            k, v = kv.split(self.config.keyvalue_separator, 1)
            try:
                data[k] = converter(v)
            except (ValueError, TypeError):
                err = ValueError(
                    f"Couldn't convert source data {v} ({type(v)}) to target type {self.config.target_type}"
                )
                if self.config.target_type_throw:
                    raise err
                else:
                    log.warning(
                        f"{err}, but target_type_throw is configured as False, continuing..."
                    )
                    continue
        return data
