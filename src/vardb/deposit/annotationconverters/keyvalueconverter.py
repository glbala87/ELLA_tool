from typing import Union, Optional, Sequence
from vardb.deposit.annotationconverters.annotationconverter import (
    AnnotationConverter,
    ElementConfig,
    TYPE_CONVERTERS,
    Primitives,
)

import logging


log = logging.getLogger(__name__)


class KeyValueConverter(AnnotationConverter):
    """Converts value to given type, and optionally splits on split_operator"""

    element_config: "ElementConfig"

    class ElementConfig(AnnotationConverter.ElementConfig):
        target_type: str = "identity"
        target_type_throw: bool = True

    def __call__(self, value: Primitives) -> Optional[Union[Primitives, Sequence[Primitives]]]:
        target_type: str = self.element_config.get("target_type", "identity")

        # target_type_throw: bool = self.element_config.get("target_type_throw", True)
        target_type_throw = self.element_config.target_type_throw
        split_operator: Optional[str] = self.element_config.get("split")

        if target_type not in TYPE_CONVERTERS:
            raise RuntimeError(
                f"Invalid target type: {target_type}. Available types are: {sorted(TYPE_CONVERTERS.keys())}"
            )

        if split_operator:
            assert isinstance(value, str), f"Cannot split source data type: {type(value)}"
            assert isinstance(
                split_operator, str
            ), f"Invalid type for split delimiter: {type(split_operator)}"
            values: Sequence[Primitives] = value.split(split_operator)

        try:
            if split_operator:
                values = [TYPE_CONVERTERS[target_type](x) for x in values]
            else:
                value = TYPE_CONVERTERS[target_type](value)
        except (ValueError, TypeError):
            if target_type_throw:
                raise ValueError(
                    f"Couldn't convert source data {value} ({type(value)}) to target type {target_type}"
                )
            else:
                log.warning(
                    f"Couldn't convert source data {value} ({type(value)}) to target type {target_type}. target_type_throw is configured as False, continuing..."
                )
                return None

        if split_operator:
            return values
        else:
            return value
