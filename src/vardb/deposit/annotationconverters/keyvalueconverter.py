import logging
from dataclasses import dataclass
from typing import Optional, Sequence, Union

from vardb.deposit.annotationconverters.annotationconverter import (
    AnnotationConverter,
    ConverterArgs,
    Primitives,
    TypeConverter,
)

log = logging.getLogger(__name__)


class KeyValueConverter(AnnotationConverter):
    """Converts value to given type, and optionally splits on self.config.split"""

    config: "Config"

    @dataclass(frozen=True)
    class Config(AnnotationConverter.Config):
        target_mode: str = "insert"
        split: Optional[str] = None
        target_type: str = "identity"
        target_type_throw: bool = True

    def __call__(self, args: ConverterArgs) -> Optional[Union[Primitives, Sequence[Primitives]]]:
        try:
            converter = TypeConverter[self.config.target_type]
        except KeyError:
            raise KeyError(
                f"Invalid target type: {self.config.target_type}. Available types are: {sorted(c.name for c in TypeConverter)}"
            )

        try:
            if self.config.split:
                assert isinstance(
                    args.value, str
                ), f"KeyValueConverter cannot split non-string on {self.config.split}: {args.value} ({type(args.value)})"
                return [converter(x) for x in args.value.split(self.config.split)]
            else:
                return converter(args.value)
        except (ValueError, TypeError):
            err = ValueError(
                f"Couldn't convert source data {args.value!r} ({type(args.value)}) to target type {self.config.target_type}"
            )
            if self.config.target_type_throw:
                raise err
            else:
                log.warning(f"{err}, but target_type_throw is configured as False, continuing...")
                return None
