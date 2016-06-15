import pytest
import os
import json
from jsonschema import validate, ValidationError


@pytest.fixture()
def schema():
    filename = '../genap-genepanel-config-schema.json'
    abs_filename = os.path.join(os.path.dirname(__file__), filename)
    with open(abs_filename) as schema_file:
        return json.load(schema_file)


def test_validates_config(schema):
    validate({"meta": {"version": "1", "updatedBy": "Erik", "updatedAt": "now"},
              "data": {}}, schema)
    assert True


def test_raises_exception_when_config_is_bad(schema):
    # illegal character in gene symbol
    with pytest.raises(ValidationError):
        validate({"meta": {"version": "1", "updatedBy": "Erik", "updatedAt": "now"},
                  "data": {"?badsymbol": {}}}, schema)

    # missing 'data'
    with pytest.raises(ValidationError):
        validate({"meta": {"version": "1", "updatedBy": "Erik", "updatedAt": "now"},
                  }, schema)

    # bad disease mode
    with pytest.raises(ValidationError):
        validate({"meta": {"version": "1", "updatedBy": "Erik", "updatedAt": "now"},
                  "data": {"BRCA1": {"disease_mode": 'unknown'}}}, schema)
