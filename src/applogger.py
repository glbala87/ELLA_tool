import os
import logging
import logging.config
import yaml

SCRIPT_DIR = os.path.abspath(os.path.dirname(__file__))


def setup_logger():
    with open(os.path.join(SCRIPT_DIR, "logconfig.yaml"), "r") as file:
        config = yaml.safe_load(file.read())
        logging.config.dictConfig(config)
