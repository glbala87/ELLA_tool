import base64
import json
import pytest
from conftest import cc
from vardb.deposit.annotationconverters import ConverterArgs, JSONConverter


@pytest.mark.parametrize("encoding", ["base16", "base32", "base64"])
def test_jsonconverter(encoding):
    encoder = {
        "base16": base64.b16encode,
        "base32": base64.b32encode,
        "base64": base64.b64encode,
    }[encoding]
    data_dict = {"a1": {"b1": {"c": [1, 2, 3]}, "b2": {"d": "dabla"}}, "a2": ["foo", "bar", "baz"]}
    data_encoded = encoder(json.dumps(data_dict).encode())
    element_config = cc.json(encoding=encoding)
    converter = JSONConverter(config=element_config)

    processed = converter(ConverterArgs(data_encoded))
    assert processed == data_dict

    subpaths = {
        "a1": data_dict["a1"],
        "a2": data_dict["a2"],
        "a1.b1": data_dict["a1"]["b1"],
        "a1.b2": data_dict["a1"]["b2"],
        "a1.b1.c": data_dict["a1"]["b1"]["c"],
        "a1.b2.d": data_dict["a1"]["b2"]["d"],
        "doesnotexist": None,
        "a1.b1.doesnotexist": None,
    }

    for subpath, expected_result in subpaths.items():
        element_config = cc.json(encoding=encoding, subpath=subpath)
        converter = JSONConverter(config=element_config)
        processed = converter(ConverterArgs(data_encoded))
        assert processed == expected_result, f"{subpath}"
