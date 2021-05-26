from typing import Dict, Any
import json
import base64

from vardb.deposit.annotationconverters.annotationconverter import AnnotationConverter


def extract_path(self, obj: Dict[str, Any], path: str) -> Any:
    if path == ".":
        return obj
    parts = path.split(".")
    next_obj: Any = obj
    while parts and next_obj is not None:
        p = parts.pop(0)
        next_obj = next_obj.get(p)
    return next_obj


DECODERS = {
    "base16": lambda x: base64.b16decode(x).decode(encoding="utf-8", errors="strict"),
    "base32": lambda x: base64.b32decode(x).decode(encoding="utf-8", errors="strict"),
    "base64": lambda x: base64.b64decode(x).decode(encoding="utf-8", errors="strict"),
}


class JSONConverter(AnnotationConverter):
    "Decode base16/base32/base64 encoded JSON strings"

    def __call__(self, value: str, additional_values: None = None) -> Dict:
        decoder_name = self.element_config.get("encoding", "base16")
        assert (
            decoder_name in DECODERS
        ), f"Unknown decoder name: {decoder_name}. Available decoders are {list(DECODERS.keys())}"
        decoder = DECODERS[decoder_name]
        data = json.loads(decoder(value))

        subpath = self.element_config.get("subpath")
        if subpath:
            keys = subpath.split(".")
            for k in keys:
                assert isinstance(
                    data, dict
                ), f"Unable to extract subpaths from {data} (of type {type(data)})"
                data = data.get(k)
                if data is None:
                    break

        return data
