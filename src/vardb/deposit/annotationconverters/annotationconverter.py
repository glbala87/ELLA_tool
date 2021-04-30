from distutils.util import strtobool

TYPE_CONVERTERS = {
    "int": lambda x: int(x),
    "float": lambda x: float(x),
    "string": lambda x: str(x),
    "bool": lambda x: bool(strtobool(x) if isinstance(x, str) else x),
    "identity": lambda x: x,
}


class AnnotationConverter:
    def __init__(self, meta, element_config):
        self.meta = meta
        self.element_config = element_config

    def setup(self):
        "Code here will be executed before first __call__"
        pass

    def __call__(self, value, additional_values=None):
        raise NotImplementedError("Must be implemented in subclass")
