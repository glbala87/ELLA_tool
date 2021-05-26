from distutils.util import strtobool
from typing import Any, Dict, Callable, Union, Optional

Primitives = Union[str, int, float, bool]
TYPE_CONVERTERS: Dict[str, Callable[[Primitives], Primitives]] = {
    "int": lambda x: int(x),
    "float": lambda x: float(x),
    "string": lambda x: str(x),
    "bool": lambda x: bool(strtobool(x) if isinstance(x, str) else x),
    "identity": lambda x: x,
}


class AnnotationConverter:
    def __init__(self, meta: Optional[Dict[str, str]], element_config: Dict[str, Any]):
        self.meta = meta
        self.element_config = element_config

    def setup(self):
        "Code here will be executed before first __call__"
        pass

    # Type hints omitted to avoid stupid mypy errors
    # value type: Union[int, str, float, bool, Tuple[Union[int, str, float, bool]]]
    # additional_values type: Dict[str, Union[int, str, float, bool, Tuple[Union[int, str, float, bool]]]]
    def __call__(
        self,
        value,
        additional_values=None,
    ):
        raise NotImplementedError("Must be implemented in subclass")
