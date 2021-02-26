from vardb.deposit.annotationconverters.annotationconverter import AnnotationConverter

import logging

log = logging.getLogger(__name__)


TYPE_CONVERTERS = {
    "int": lambda x: int(x),
    "float": lambda x: float(x),
    "string": lambda x: str(x),
    "bool": lambda x: bool(x),
}


class KeyValueConverter(AnnotationConverter):
    def __call__(self, value, **kwargs):
        target_type = self.element_config["target_type"]
        target_type_throw = self.element_config.get("target_type_throw", True)
        split_operator = self.element_config.get("split")

        # Workaround vcfiterator parsing Number=A as list (we always work on single allelic data)
        if isinstance(value, list) and len(value) == 1:
            value = value[0]

        if target_type not in TYPE_CONVERTERS:
            raise RuntimeError(
                f"Invalid target type: {target_type}. Available types are: {sorted(TYPE_CONVERTERS.keys())}"
            )

        try:
            source_data = TYPE_CONVERTERS[target_type](value)
        except ValueError:
            if target_type_throw:
                raise RuntimeError(
                    f"Couldn't convert source data {value} ({type(value)}) to target type {target_type}"
                )
            else:
                log.warning(
                    f"Couldn't convert source data {value} ({type(value)}) to target type {target_type}. target_type_throw is configured as False, continuing..."
                )
                return

        if split_operator:
            if not isinstance(source_data, str):
                raise RuntimeError(f"Cannot split source data type: {type(source_data)}")
            if not isinstance(split_operator, str):
                raise RuntimeError(f"Invalid type for split delimiter: {type(split_operator)}")
            source_data = source_data.split(split_operator)

        return source_data
