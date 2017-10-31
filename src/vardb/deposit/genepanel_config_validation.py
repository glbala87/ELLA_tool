import os
from jsonschema import validate, FormatChecker
import json


SCHEMA_VERSION_1 = "1"
SCHEMA_VERSION_2 = "2"

SCHEMA_VERSIONS = {
    SCHEMA_VERSION_1: '../datamodel/genepanel-config-schema.json',
    SCHEMA_VERSION_2: '../datamodel/genepanel-config-schema_v2.json'
}


def config_valid(config, version=SCHEMA_VERSION_2):
    version = SCHEMA_VERSION_2 if not version else version
    name_of_schema_file = os.path.join(os.path.dirname(__file__), SCHEMA_VERSIONS[version])
    with open(name_of_schema_file) as schema_file:
        my_schema = json.load(schema_file)
        # see doc http://python-jsonschema.readthedocs.io/en/latest/validate/#validating-formats
        validate(config, my_schema, format_checker=FormatChecker())

    return True
