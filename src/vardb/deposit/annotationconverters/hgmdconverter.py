from dataclasses import dataclass
import re
from vardb.deposit.annotationconverters.annotationconverter import (
    AnnotationConverter,
    ConverterArgs,
)
from typing import Dict


# HGMD data can come with character sequences to represent characters with
# special meaning in VCF
_HGMD_SUBSTITUTE = [
    (re.compile(r"@#EQ"), "="),
    (re.compile(r"@#CM"), ","),
    (re.compile(r"@#SC"), ";"),
    (re.compile(r"@#SP"), " "),
    (re.compile(r"@#TA"), "\t"),
]


def _translate_to_original(x: str) -> str:
    if not isinstance(x, str):
        return x
    for regexp, substitution in _HGMD_SUBSTITUTE:
        x = regexp.sub(substitution, x)
    return x


class HGMDConverter(AnnotationConverter):
    config: "Config"

    @dataclass(frozen=True)
    class Config(AnnotationConverter.Config):
        pass

    def __call__(self, args: ConverterArgs) -> Dict[str, str]:
        assert isinstance(
            args.value, str
        ), f"Invalid parameter for HGMDConverter: {args.value} ({type(args.value)})"
        assert (
            args.additional_values is not None
        ), f"HGMDConverter cannot have None for args.additional_values"

        disease: str = args.additional_values["HGMD__disease"]
        tag: str = args.additional_values["HGMD__tag"]

        assert tag == _translate_to_original(tag)
        assert args.value == _translate_to_original(args.value)

        return {"acc_num": args.value, "disease": _translate_to_original(disease), "tag": tag}
