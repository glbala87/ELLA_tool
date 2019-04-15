import os
import logging
import argparse
import json
from vardb.datamodel import DB, assessment

"""
Update reference database in E||A by deposit of new references and
updating old references.
"""

SCRIPT_DIR = os.path.abspath(os.path.dirname(__file__))
BATCH_SIZE = 200  # Determine number of references to query at a time
log = logging.getLogger(__name__)


def get_reference_batches(f):
    """
    :param f: Open file object with one json reference per line
    :yield : list of dict references
    """
    # Initialize empty batch of references
    reference_batch = []
    # Get all full batches
    for reference in f:
        reference_as_dict = json.loads(reference)
        reference_batch.append(reference_as_dict)
        if len(reference_batch) >= BATCH_SIZE:
            yield reference_batch
            reference_batch = []

    # Get partially filled batch
    if reference_batch:
        yield reference_batch


def import_references(session, filename):
    """
    :param session: an sqlalchemy 'session' of E||A database
    :param filename: a file with one json-formatted reference per line
    :return : update E||A database with references from 'filename'
    """
    log.info("Importing references from %s" % filename)
    created = 0
    updated = 0
    with open(filename) as f:
        for reference_batch in get_reference_batches(f):
            # Query by pubmed_id to get list of pointers to existing_references
            pmids = [ref["pubmed_id"] for ref in reference_batch]
            existing_references = (
                session.query(assessment.Reference)
                .filter(assessment.Reference.pubmed_id.in_(pmids))
                .all()
            )
            existing_pmids = [ref.pubmed_id for ref in existing_references]

            for reference in reference_batch:
                existing_reference = next(
                    (er for er in existing_references if er.pubmed_id == reference["pubmed_id"]),
                    None,
                )
                if existing_reference:
                    updated += 1
                    for key, value in reference.items():
                        setattr(existing_reference, key, value)
                else:
                    created += 1
                    session.add(assessment.Reference(**reference))

            session.commit()

    log.info(
        "References successfully imported (created: {created}, updated: {updated})!".format(
            created=created, updated=updated
        )
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Deposit references from file")
    parser.add_argument(
        "json_file", type=str, help="relative path to file containing list of references"
    )
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO)

    filename = os.path.abspath(args.json_file)
    # Import argparse, add CLI for getting path to JSON file.
    db = DB()
    db.connect()
    import_references(db.session, filename)
