import os
import logging
import argparse
import json
from vardb.datamodel import DB, annotation

"""
Populate customannotation database in E||A
"""

SCRIPT_DIR = os.path.abspath(os.path.dirname(__file__))
log = logging.getLogger(__name__)


def get_custom_annotation_batches(f):
    batch = []
    for ca in f:
        ca_as_dict = json.loads(ca)
        batch.append(ca_as_dict)
    return batch


def import_custom_annotations(session, filename):
    """
    :param session: an sqlalchemy 'session' of E||A database
    :param filename: a file with one json-formatted custom annotation per line
    :return : update E||A database with annotations from 'filename'
    """
    log.info("Importing custom annotations from %s" % filename)
    with open(filename) as f:
        for ca in get_custom_annotation_batches(f):
            log.info("Adding custom annotation")
            session.add(annotation.CustomAnnotation(**ca))
        session.commit()

    log.info("Custom annotations successfully imported!")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Deposit custom annotations from file")
    parser.add_argument(
        "json_file", type=str, help="relative path to file containing list of custom annotations"
    )
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO)

    filename = os.path.abspath(args.json_file)
    # Import argparse, add CLI for getting path to JSON file.
    db = DB()
    db.connect()
    import_custom_annotations(db.session, filename)
