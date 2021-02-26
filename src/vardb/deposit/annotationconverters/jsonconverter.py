from typing import Dict, Any
import json
import base64
import jsonschema

from vardb.deposit.annotationconverters.annotationconverter import AnnotationConverter

import logging

log = logging.getLogger(__name__)


def extract_path(self, obj: Dict[str, Any], path: str) -> Any:
    if path == ".":
        return obj
    parts = path.split(".")
    next_obj: Any = obj
    while parts and next_obj is not None:
        p = parts.pop(0)
        next_obj = next_obj.get(p)
    return next_obj


CLINVAR_V1_INCOMING_SCHEMA = {
    "definitions": {
        "rcv": {
            "$id": "#/definitions/rcv",
            "type": "object",
            "required": [
                "traitnames",
                "clinical_significance_descr",
                "variant_id",
                "submitter",
                "last_evaluated",
            ],
            "properties": {
                "traitnames": {"type": "array", "items": {"type": "string"}},
                "clinical_significance_descr": {"type": "array", "items": {"type": "string"}},
                "variant_id": {"type": "array", "items": {"type": "string"}},
                "submitter": {"type": "array", "items": {"type": "string"}},
            },
        }
    },
    "$schema": "http://json-schema.org/draft-07/schema#",
    "$id": "http://example.com/root.json",
    "type": "object",
    "required": ["variant_description", "variant_id", "rcvs"],
    "properties": {
        "variant_description": {"$id": "#/properties/variant_description", "type": "string"},
        "variant_id": {"$id": "#/properties/variant_id", "type": "integer"},
        "rcvs": {"type": "object", "patternProperties": {"": {"$ref": "#/definitions/rcv"}}},
    },
}


def _convert_clinvar_v1(clinvarjson):
    CLINVAR_FIELDS = ["variant_description", "variant_id"]
    CLINVAR_RCV_FIELDS = [
        "traitnames",
        "clinical_significance_descr",
        "variant_id",
        "submitter",
        "last_evaluated",
    ]
    data = dict(items=[])
    data.update({k: clinvarjson[k] for k in CLINVAR_FIELDS})

    for rcv, val in list(clinvarjson["rcvs"].items()):
        item = {k: ", ".join(val[k]) for k in CLINVAR_RCV_FIELDS}
        item["rcv"] = rcv
        data["items"].append(item)

    return data


def convert_clinvar(annotation):
    if "CLINVARJSON" not in annotation:
        return dict()

    clinvarjson = json.loads(
        base64.b16decode(annotation["CLINVARJSON"]).decode(encoding="utf-8", errors="strict")
    )
    # Legacy: In version 1 of the ClinVar data, we performed additional parsing of the clinvar data.
    # The validation of the resulting clinvar json is done in the database.
    try:
        jsonschema.validate(clinvarjson, CLINVAR_V1_INCOMING_SCHEMA)
        return {"CLINVAR": _convert_clinvar_v1(clinvarjson)}
    except jsonschema.ValidationError:
        return {"CLINVAR": clinvarjson}


DECODERS = {
    "base16": lambda x: base64.b16decode(x).decode(encoding="utf-8", errors="strict"),
    "base32": lambda x: base64.b32decode(x).decode(encoding="utf-8", errors="strict"),
    "base64": lambda x: base64.b16decode(x).decode(encoding="utf-8", errors="strict"),
    "identity": lambda x: x,
}


class JSONConverter(AnnotationConverter):
    def __call__(self, value, additional_values=None):
        decoder_name = self.element_config.get("encoding", "identitiy")
        decoder = DECODERS[decoder_name]
        data = json.loads(decoder(value))
        # TODO: Update testdata, then we can remove clinvar_v1 check
        try:
            jsonschema.validate(data, CLINVAR_V1_INCOMING_SCHEMA)
            data = _convert_clinvar_v1(data)
        except:
            pass

        subpath = self.element_config.get("subpath")
        if subpath:
            keys = subpath.split(".")
            for k in keys:
                data = data.get(k)
                if data is None:
                    break

        return data
