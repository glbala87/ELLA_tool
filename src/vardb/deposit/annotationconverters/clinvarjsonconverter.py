import jsonschema
from typing import Dict
from vardb.deposit.annotationconverters.jsonconverter import JSONConverter

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


class CLINVARJSONConverter(JSONConverter):
    def __call__(
        self,
        value: str,
        additional_values: None = None,
    ) -> Dict:
        # TODO: The ClinVar data is a mess. We convert data in the new format (conforming to the schema)
        # to the "old" format. This should get a proper overhaul.
        data = super(self.__class__, self).__call__(value, additional_values)
        try:
            jsonschema.validate(data, CLINVAR_V1_INCOMING_SCHEMA)
            data = _convert_clinvar_v1(data)
        except jsonschema.ValidationError:
            pass
        return data
