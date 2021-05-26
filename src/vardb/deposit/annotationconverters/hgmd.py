import re
from .annotationconverter import AnnotationConverter
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
    def __call__(self, acc_num: str, additional_values: Dict[str, str] = None) -> Dict[str, str]:
        assert additional_values is not None
        disease = additional_values["HGMD__disease"]
        tag = additional_values["HGMD__tag"]

        assert tag == _translate_to_original(tag)
        assert acc_num == _translate_to_original(acc_num)

        return {"acc_num": acc_num, "disease": _translate_to_original(disease), "tag": tag}
