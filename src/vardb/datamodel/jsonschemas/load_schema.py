import os
import json

SCRIPT_PATH = os.path.dirname(os.path.realpath(__file__))


def load_schema(schemaname):
    with open(os.path.join(SCRIPT_PATH, schemaname)) as f:
        return json.load(f)
