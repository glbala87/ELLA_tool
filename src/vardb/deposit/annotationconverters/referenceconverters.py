import re
import logging
import json
import base64
from typing import Dict, List, Union

from .annotationconverter import AnnotationConverter

log = logging.getLogger(__name__)

REFTAG: Dict[str, str] = {
    "APR": "Additional phenotype",
    "FCR": "Functional characterisation",
    "MCR": "Molecular characterisation",
    "SAR": "Additional report",
}

_HGMD_SUBSTITUTE = [
    (re.compile(r"@#EQ"), "="),
    (re.compile(r"@#CM"), ","),
    (re.compile(r"@#SC"), ";"),
    (re.compile(r"@#SP"), " "),
    (re.compile(r"@#TA"), "\t"),
]


def _translate_hgmd(x: str) -> str:
    if not isinstance(x, str):
        return x
    for regexp, substitution in _HGMD_SUBSTITUTE:
        x = regexp.sub(substitution, x)
    return x


class HGMDPrimaryReportConverter(AnnotationConverter):
    def __call__(
        self,
        value: str,
        additional_values: Dict[str, str] = None,
    ) -> List[Dict[str, Union[str, int]]]:
        try:
            pmid = int(value)
        except ValueError:
            log.warning("Cannot convert pubmed id from annotation to integer: {}".format(value))
            return []

        reftag = "Primary literature report"
        if additional_values and additional_values.get("HGMD__comments"):
            comments = additional_values["HGMD__comments"]
            comments = "No comments." if comments == "None" or not comments else comments
        else:
            comments = "No comments."
        info_string = f"{reftag}. {_translate_hgmd(comments)}"

        return [{"pubmed_id": pmid, "source": "HGMD", "source_info": info_string}]


class HGMDExtraRefsConverter(AnnotationConverter):
    def setup(self):
        assert (
            self.meta is not None
        ), f"Unable to parse HGMD extra references without description of {self.element_config['source']} in VCF header"
        self.extraref_keys = re.findall(r"Format: \((.*?)\)", self.meta["Description"])[0].split(
            "|"
        )

    def __call__(
        self,
        value: str,
        additional_values: None = None,
    ) -> List[Dict[str, Union[str, int]]]:

        references: List[Dict[str, Union[str, int]]] = []

        for extraref in value.split(","):
            er_data = dict(zip(self.extraref_keys, extraref.split("|")))
            try:
                pmid = int(er_data["pmid"])
            except ValueError:
                log.warning("Cannot convert pubmed id from annotation to integer: {}".format(pmid))
                continue

            reftag = REFTAG.get(er_data.get("reftag", "N/A"), "Reftag not specified")
            comments = er_data.get("comments", "No comments.")
            comments = "No comments." if not comments else comments

            # The comment on APR is the disease/phenotype
            if er_data.get("reftag") == "APR" and comments == "No comments.":
                comments = er_data.get("disease", comments)

            info_string = f"{reftag}. {_translate_hgmd(comments)}"

            references.append({"pubmed_id": pmid, "source": "HGMD", "source_info": info_string})

        return references


class ClinVarReferencesConverter(AnnotationConverter):
    def __call__(
        self,
        value: str,
        additional_values: None = None,
    ) -> List[Dict[str, Union[int, str]]]:
        clinvarjson = json.loads(base64.b16decode(value).decode(encoding="utf-8", errors="strict"))

        pubmeds: List[str] = clinvarjson.get("pubmeds", [])
        pubmeds += clinvarjson.get("pubmed_ids", [])
        references: List[Dict[str, Union[int, str]]] = [
            {"pubmed_id": int(pmid), "source": "CLINVAR", "source_info": ""} for pmid in pubmeds
        ]

        return references
