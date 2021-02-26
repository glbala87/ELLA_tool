class AnnotationConverter:
    def __init__(self, meta, element_config):
        self.meta = meta
        self.element_config = element_config

    def setup(self):
        "Code here will be executed before first __call__"
        pass

    def __call__(self, value, additional_values=None):
        raise NotImplementedError("Must be implemented in subclass")
