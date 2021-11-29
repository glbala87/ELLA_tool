from dataclasses import dataclass, field
from distutils.util import strtobool
from enum import Enum, auto
from typing import Any, List, Mapping, Optional, Sequence, Union

from vardb.util.vcfrecord import Primitives


class TypeConverter(Enum):
    int = auto()
    float = auto()
    str = auto()
    bool = auto()
    identity = auto()
    # use string as alias for str so can use builtin func directly
    # i.e., TypeConverter.string.name == "str"
    string = str

    def __call__(self, val: Any) -> Primitives:
        if self is TypeConverter.identity:
            return val
        elif self is TypeConverter.bool:
            return bool(strtobool(val) if isinstance(val, str) else val)
        else:
            if isinstance(val, str):
                # eval f-string needs quotes so value of val not interpreted as variable name
                return eval(f"{self.name}('{val}')")
            else:
                return eval(f"{self.name}({val})")


@dataclass(frozen=True)
class ConverterArgs:
    value: Union[Primitives, Sequence[Primitives]]
    additional_values: Optional[Mapping[str, Any]] = None


class AnnotationConverter:
    meta: Optional[Mapping[str, str]]
    config: "Config"

    @dataclass(frozen=True, init=False)
    class Config:
        source: str
        target: str
        target_mode: str = "insert"
        additional_sources: List[str] = field(default_factory=list)

        def __init__(self, *args, **kwargs) -> None:
            raise NotImplementedError("Config class must be implemented in subclasss")

    def __init__(self, config: Config, meta: Mapping[str, str] = None):
        self.config = config
        self.meta = meta

    def setup(self):
        "Code here will be executed before first __call__"
        pass

    def __call__(self, args: ConverterArgs):
        raise NotImplementedError("Must be implemented in subclass")
