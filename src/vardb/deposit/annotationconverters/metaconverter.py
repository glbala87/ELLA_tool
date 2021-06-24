import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Mapping, Optional, Sequence, Union

from vardb.deposit.annotationconverters.annotationconverter import (
    AnnotationConverter,
    ConverterArgs,
    Primitives,
)
from vardb.deposit.annotationconverters.keyvalueconverter import KeyValueConverter


class MetaConverter(AnnotationConverter):
    """Meta converter, using a pattern in the Description to fetch key-value pairs from the annotation.
    This can be used to fetch data from annotations like e.g. VEPs CSQ field or SpliceAI, which are pipe-separated
    values, with keys provided in the description. Subelements can be used to extract only a subset of the keys."""

    config: "Config"
    keys: Sequence[str]
    subconfigs: Mapping[str, KeyValueConverter.Config]

    @dataclass(frozen=True)
    class Config(AnnotationConverter.Config):
        subelements: List[Dict[str, Any]] = field(default_factory=list)
        list_separator: Optional[str] = None
        value_separator: str = "|"
        meta_pattern: str = r"(?i)[a-z_]+\|[a-z_\|]+"

    def setup(self):
        "Parse Description field of the meta header"
        assert (
            self.meta is not None
        ), f"Unable to parse without meta info for {self.config.source} in VCF header"

        pattern = self.config.meta_pattern
        pattern_format = re.findall(pattern, self.meta["Description"])
        assert (
            pattern_format is not None
        ), f"Did not find a match to regex {pattern} in description {self.meta['Description']}."
        assert (
            len(pattern_format) == 1
        ), f"Found multiple patterns matching {pattern} in {self.meta['Description']}"

        self.keys = pattern_format[0].split(self.config.value_separator)

        self.subconfigs = dict()
        for sub_el in self.config.subelements:
            self.subconfigs[sub_el["source"]] = KeyValueConverter.Config(
                **{
                    **dict(target=self.config.target),
                    **sub_el,
                }
            )
        assert set(self.subconfigs.keys()).issubset(
            self.keys
        ), f"Did not find description for key(s) {set(self.subconfigs.keys()) - set(self.keys)} in description {self.meta['Description']}"

    def __call__(
        self, args: ConverterArgs
    ) -> Union[Dict[str, Primitives], List[Dict[str, Primitives]]]:
        assert isinstance(
            args.value, str
        ), f"Invalid parameter for MetaConverter: {args.value} ({type(args.value)})"

        def parse_item(item):
            d = {}
            for k, v in item.items():
                if k not in self.subconfigs:
                    continue
                kvc = KeyValueConverter(config=self.subconfigs[k])
                d[k] = kvc(ConverterArgs(v))
            return d

        if self.config.list_separator:
            data = []
            for raw_item in args.value.split(self.config.list_separator):
                item = dict(zip(self.keys, raw_item.split(self.config.value_separator)))
                data.append(parse_item(item))
        else:
            raw_item = args.value
            item = dict(zip(self.keys, raw_item.split(self.config.value_separator)))
            data = parse_item(item)
        return data
