from typing import List, Dict, Any
import json
import base64

import logging

log = logging.getLogger(__name__)


class JSONConverter:
    def __init__(self, config):
        self.config = config

    def extract_path(self, obj: Dict[str, Any], path: str) -> Any:
        if path == ".":
            return obj
        parts = path.split(".")
        next_obj: Any = obj
        while parts and next_obj is not None:
            p = parts.pop(0)
            next_obj = next_obj.get(p)
        return next_obj

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

        source = self.config["source"]
        if self.config.get("required"):
            if source not in annotation:
                raise RuntimeError(f"Missing required field: {source}")

        if source not in annotation:
            return

        data = json.loads(
            base64.b16decode(annotation[source]).decode(encoding="utf-8", errors="strict")
        )

        for path in self.config["paths"]:
            source_data = self.extract_path(data, path["source"])
            if path.get("required") and source_data is None:
                raise RuntimeError(f"Missing required key: {source} for path {path}")
            self.insert_at_path(annotations, path["target"], source_data)
