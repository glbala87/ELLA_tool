from dataclasses import dataclass
from distutils.util import strtobool
from typing import Any, Callable, Mapping, Union, Optional

Primitives = Union[str, int, float, bool]
TYPE_CONVERTERS: Mapping[str, Callable[[Primitives], Primitives]] = {
    "int": lambda x: int(x),
    "float": lambda x: float(x),
    "string": lambda x: str(x),
    "bool": lambda x: bool(strtobool(x) if isinstance(x, str) else x),
    "identity": lambda x: x,
}


@dataclass(frozen=True)
class ConverterArgs:
    value: Any
    additional_values: Mapping[str, Any]


class AnnotationConverter:
    @dataclass
    class ElementConfig:
        def __init__(self, *args, **kwargs) -> None:
            raise NotImplementedError("aadsgsadhds")

    meta: Optional[Mapping[str, str]]
    element_config: ElementConfig

    def __init__(self, meta: Optional[Mapping[str, str]], element_config: ElementConfig):
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
        args: ConverterArgs,
    ):
        raise NotImplementedError("Must be implemented in subclass")
