import logging
import logging.config
import yaml
from pathlib import Path

SCRIPT_DIR = Path(__file__).absolute().parent


def setup_logger():
    with open(SCRIPT_DIR / "logconfig.yaml", "r") as file:
        config = yaml.safe_load(file.read())
        logging.config.dictConfig(config)
