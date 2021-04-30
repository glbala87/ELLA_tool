from vardb.deposit.annotationconverters.annotationconverter import AnnotationConverter
from vardb.deposit.annotationconverters.keyvalueconverter import KeyValueConverter
import re


class MetaConverter(AnnotationConverter):
    """Meta converter, using a pattern in the Description to fetch key-value pairs from the annotation.
    This can be used to fetch data from annotations like e.g. VEPs CSQ field or SpliceAI, which are pipe-separated
    values, with keys provided in the description"""

    def setup(self):
        "Parse Description field of the meta header"
        assert (
            self.meta is not None
        ), f"Unable to parse without meta info for {self.element_config['source']} in VCF header"

        pattern = self.element_config.get("meta_pattern", r"(?i)[a-z_]+\|[a-z_\|]+")
        pipe_format = re.findall(pattern, self.meta["Description"])
        assert (
            pipe_format is not None
        ), f"Did not find a match to regex {pattern} in description {self.meta['Description']}."
        assert len(pipe_format) == 1, "Found multiple pipe separated"

        self.keys = pipe_format[0].split(self.element_config.get("value_separator", "|"))

        self.subconfigs = {x["source"]: x for x in self.element_config["subelements"]}
        assert set(self.subconfigs.keys()).issubset(
            self.keys
        ), f"Did not find description for key(s) {set(self.subconfigs.keys()) - set(self.keys)} in description {self.meta['Description']}"

    def __call__(self, value, **kwargs):
        list_separator = self.element_config.get("list_separator")
        value_separator = self.element_config.get("value_separator", "|")

        def parse_item(item):
            d = {}
            for k, v in item.items():
                if k not in self.subconfigs:
                    continue
                kvc = KeyValueConverter(None, self.subconfigs[k])
                d[k] = kvc(v)
            return d

        if list_separator:
            data = []
            for raw_item in value.split(list_separator):
                item = dict(zip(self.keys, raw_item.split(value_separator)))
                data.append(parse_item(item))
        else:
            raw_item = value
            item = dict(zip(self.keys, raw_item.split(value_separator)))
            data = parse_item(item)
        return data
