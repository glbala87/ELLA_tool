import base64
import json
import logging
import re
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Union

from vardb.deposit.annotationconverters.annotationconverter import (
    AnnotationConverter,
    ConverterArgs,
)

log = logging.getLogger(__name__)


class RefTag(str, Enum):
    def __str__(self) -> str:
        return self.value

    @classmethod
    def tag_strings(cls) -> List[str]:
        """Lists tags as they appear in HGMD, only used in testing"""
        return ["" if rt is RefTag.NA else rt.name for rt in cls]

    NA = "Reftag not specified"
    APR = "Additional phenotype"
    FCR = "Functional characterisation"
    MCR = "Molecular characterisation"
    SAR = "Additional report"
    # NOTE: Have also seen ACR in test data, but no definition. How should this be treated?


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
    config: "Config"

    @dataclass(frozen=True)
    class Config(AnnotationConverter.Config):
        pass

    def __call__(self, args: ConverterArgs) -> List[Dict[str, Union[str, int]]]:
        assert isinstance(
            args.value, (int, str)
        ), f"Invalid parameter for HGMDPrimaryReportConverter: {args.value} ({type(args.value)})"
        assert args.additional_values is not None
        try:
            pmid = int(args.value)
        except ValueError:
            log.warning(
                "Cannot convert pubmed id from annotation to integer: {}".format(args.value)
            )
            return []

        reftag = "Primary literature report"
        if args.additional_values.get("HGMD__comments"):
            comments = args.additional_values["HGMD__comments"]
            comments = "No comments." if comments == "None" or not comments else comments
        else:
            comments = "No comments."
        info_string = f"{reftag}. {_translate_hgmd(comments)}"

        return [{"pubmed_id": pmid, "source": "HGMD", "source_info": info_string}]


class HGMDExtraRefsConverter(AnnotationConverter):
    config: "Config"

    @dataclass(frozen=True)
    class Config(AnnotationConverter.Config):
        pass

    def setup(self):
        assert (
            self.meta is not None
        ), f"Unable to parse HGMD extra references without description of {self.element_config['source']} in VCF header"
        self.extraref_keys = re.findall(r"Format: \((.*?)\)", self.meta["Description"])[0].split(
            "|"
        )

    def __call__(self, args: ConverterArgs) -> List[Dict[str, Union[str, int]]]:
        assert isinstance(
            args.value, str
        ), f"Invalid parameter for HGMDExtraRefsConverter: {args.value} ({type(args.value)})"
        references: List[Dict[str, Union[str, int]]] = []

        for extraref in args.value.split(","):
            er_data = dict(zip(self.extraref_keys, extraref.split("|")))
            try:
                pmid = int(er_data["pmid"])
            except ValueError:
                log.warning(
                    "Cannot convert pubmed id from annotation to integer: {}".format(
                        er_data["pmid"]
                    )
                )
                continue

            reftag_str = er_data.get("reftag")
            if reftag_str:
                try:
                    reftag = RefTag[reftag_str]
                except KeyError:
                    log.warning(f"Got unknown reftag: {reftag_str}, treating like NA")
                    reftag = RefTag.NA
            else:
                # empty string, None
                reftag = RefTag.NA

            comments = er_data.get("comments", "No comments.")
            comments = "No comments." if not comments else comments

            # The comment on APR is the disease/phenotype
            if reftag is RefTag.APR and comments == "No comments.":
                comments = er_data.get("disease", comments)

            info_string = f"{reftag}. {_translate_hgmd(comments)}"

            references.append({"pubmed_id": pmid, "source": "HGMD", "source_info": info_string})

        return references


class ClinVarReferencesConverter(AnnotationConverter):
    config: "Config"

    @dataclass(frozen=True)
    class Config(AnnotationConverter.Config):
        pass

    def __call__(self, args: ConverterArgs) -> List[Dict[str, Union[int, str]]]:
        assert isinstance(
            args.value, (str, bytes)
        ), f"Invalid parameter for ClinVarReferencesConverter: {args.value} ({type(args.value)})"

        clinvarjson: Dict[str, Any] = json.loads(
            base64.b16decode(args.value).decode(encoding="utf-8", errors="strict")
        )

        pubmeds: List[str] = clinvarjson.get("pubmeds", [])
        pubmeds += clinvarjson.get("pubmed_ids", [])
        references: List[Dict[str, Union[int, str]]] = [
            {"pubmed_id": int(pmid), "source": "CLINVAR", "source_info": ""} for pmid in pubmeds
        ]

        return references
