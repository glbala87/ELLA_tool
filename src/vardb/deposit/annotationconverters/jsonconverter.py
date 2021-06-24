import base64
import json
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Optional, Union

from vardb.deposit.annotationconverters.annotationconverter import (
    AnnotationConverter,
    ConverterArgs,
)


def extract_path(self, obj: Dict[str, Any], path: str) -> Any:
    if path == ".":
        return obj
    parts = path.split(".")
    next_obj: Any = obj
    while parts and next_obj is not None:
        p = parts.pop(0)
        next_obj = next_obj.get(p)
    return next_obj


class Decoder(str, Enum):
    base16 = "b16decode"
    base32 = "b32decode"
    base64 = "b64decode"

    @classmethod
    def names(cls) -> List[str]:
        return [e.name for e in cls]

    def __call__(self, val: Union[bytes, str]) -> str:
        if isinstance(val, str):
            val = val.encode("UTF-8", "strict")
        return getattr(base64, self.value)(val).decode(encoding="utf-8", errors="strict")


class JSONConverter(AnnotationConverter):
    "Decode base16/base32/base64 encoded JSON strings"
    config: "Config"

    @dataclass(frozen=True)
    class Config(AnnotationConverter.Config):
        encoding: str = "base16"
        subpath: Optional[str] = None

        @property
        def decoder(self):
            return Decoder[self.encoding]

    def setup(self) -> None:
        if self.config.encoding not in [d.name for d in Decoder]:
            raise ValueError(
                f"Invalid encoding: {self.config.encoding}. Must be one of: {', '.join(Decoder.names())}"
            )

    def __call__(self, args: ConverterArgs) -> Dict:
        assert isinstance(
            args.value, (str, bytes)
        ), f"Invalid parameter for JSONConverter: {args.value} ({type(args.value)})"

        decoder = Decoder[self.config.encoding]
        data = json.loads(decoder(args.value))

        if self.config.subpath:
            keys = self.config.subpath.split(".")
            for k in keys:
                assert isinstance(
                    data, dict
                ), f"Unable to extract subpaths from {data} (of type {type(data)})"
                data = data.get(k)
                if data is None:
                    break

        return data
