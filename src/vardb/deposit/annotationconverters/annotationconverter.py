from distutils.util import strtobool
from typing import Any, Dict, Optional

TYPE_CONVERTERS = {
    "int": lambda x: int(x),
    "float": lambda x: float(x),
    "string": lambda x: str(x),
    "bool": lambda x: bool(strtobool(x) if isinstance(x, str) else x),
    "identity": lambda x: x,
}


class AnnotationConverter:
    def __init__(self, meta: Dict[str, Any], element_config: Dict[str, Any]):
        self.meta = meta
        self.element_config = element_config

    def setup(self):
        "Code here will be executed before first __call__"
        pass

    def __call__(self, value: str, additional_values: Optional[Dict[str, str]] = None):
        raise NotImplementedError("Must be implemented in subclass")
