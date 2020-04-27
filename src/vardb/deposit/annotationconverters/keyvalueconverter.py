from typing import Dict, Any
import json
import base64

import logging

log = logging.getLogger(__name__)


TYPE_CONVERTERS = {
    "int": lambda x: int(x),
    "float": lambda x: float(x),
    "string": lambda x: str(x),
    "bool": lambda x: bool(x),
}


class KeyValueConverter:
    def __init__(self, config):
        self.config = config

    def insert_at_path(self, obj: Dict[str, Any], path: str, item: Any) -> Any:
        if path == ".":
            return obj
        parts = path.split(".")
        next_obj = obj
        while parts and next_obj != item:
            p = parts.pop(0)
            if p not in next_obj:
                next_obj[p] = {} if parts else item
            next_obj = next_obj[p]

    def convert(self, annotation, annotations):

        for source_config in self.config["sources"]:
            source = source_config["source"]
            target = source_config["target"]
            required = source_config.get("required", False)
            target_type = source_config["target_type"]
            target_type_throw = source_config.get("target_type_throw", True)
            split_operator = source_config.get("split")

            if source not in annotation:
                if required:
                    raise RuntimeError(f"Missing required source field in annotation: {source}")
                else:
                    continue

            source_data_raw = annotation[source]

            # Workaround vcfiterator parsing Number=A as list (we always work on single allelic data)
            if isinstance(source_data_raw, list) and len(source_data_raw) == 1:
                source_data_raw = source_data_raw[0]

            if target_type not in TYPE_CONVERTERS:
                raise RuntimeError(
                    f"Invalid target type: {target_type}. Available types are: {sorted(TYPE_CONVERTERS.keys())}"
                )

            try:
                source_data = TYPE_CONVERTERS[target_type](source_data_raw)
            except ValueError:
                if target_type_throw:
                    raise RuntimeError(
                        f"Couldn't convert source data {source_data_raw} ({type(source_data_raw)}) to target type {target_type}"
                    )
                else:
                    log.warning(
                        f"Couldn't convert source data {source_data_raw} ({type(source_data_raw)}) to target type {target_type}. target_type_throw is configured as False, continuing..."
                    )
                    continue

            if split_operator:
                if not isinstance(source_data, str):
                    raise RuntimeError(f"Cannot split source data type: {type(source_data)}")
                if not isinstance(split_operator, str):
                    raise RuntimeError(f"Invalid type for split delimiter: {type(split_operator)}")
                source_data = source_data.split(split_operator)

            self.insert_at_path(annotations, target, source_data)
