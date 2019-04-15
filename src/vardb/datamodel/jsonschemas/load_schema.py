import os

# import json
import jsonref

SCRIPT_PATH = os.path.dirname(os.path.realpath(__file__))


def load_schema(schemaname):
    loader = jsonref.JsonLoader(cache_results=False)
    with open(os.path.join(SCRIPT_PATH, schemaname)) as f:
        return jsonref.load(
            f,
            loader=loader,
            jsonschema=True,
            base_uri="file:{}/".format(SCRIPT_PATH),
            load_on_repr=True,
        )
