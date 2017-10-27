import os
from jsonschema import validate, FormatChecker
import json


def config_valid(config):
    name_of_schema_file = '../datamodel/genap-genepanel-config-schema.json'
    abs_filename = os.path.join(os.path.dirname(__file__), name_of_schema_file)

    with open(abs_filename) as schema_file:
        my_schema = json.load(schema_file)
        # see doc http://python-jsonschema.readthedocs.io/en/latest/validate/#validating-formats
        validate(config, my_schema, format_checker=FormatChecker())

    return True
