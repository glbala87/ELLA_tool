from vardb.deposit.annotationconverters.annotationconverter import (
    AnnotationConverter,
    TYPE_CONVERTERS,
)

import logging

log = logging.getLogger(__name__)


class FlatJSONConverter(AnnotationConverter):
    def __call__(self, value, additional_values=None):
        item_separator = self.element_config.get("item_separator", ",")
        keyvalue_separator = self.element_config.get("keyvalue_separator", ":")
        value_target_type = self.element_config.get("value_target_type", "string")
        value_target_type_throw = self.element_config.get("value_target_type_throw", True)
        data = {}
        for kv in value.split(item_separator):
            k, v = kv.split(keyvalue_separator, 1)
            try:
                v = TYPE_CONVERTERS[value_target_type](v)
            except (ValueError, TypeError):
                if value_target_type_throw:
                    raise ValueError(
                        f"Couldn't convert source data {v} ({type(v)}) to target type {value_target_type}"
                    )
                else:
                    log.warning(
                        f"Couldn't convert source data {v} ({type(v)}) to target type {value_target_type}. target_type_throw is configured as False, continuing..."
                    )
                    continue
            data[k] = v
        return data
