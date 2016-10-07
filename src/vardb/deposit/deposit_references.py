import os
import logging
import argparse
import json
from vardb.datamodel import DB, assessment

SCRIPT_DIR = os.path.abspath(os.path.dirname(__file__))
BATCH_SIZE = 100
log = logging.getLogger(__name__)

# Load "JSON", split lines etc...
# Take batch of N references (from JSON)
# Use session.query(assessment.Reference).filter(assessment.Reference.pubmed_id.in_(pmids).all()
# -> [Reference(), ... ]
# Split your list into existing and new

# Loop over json_file list objects, check whether an DB object exists.
# If so, update the object by reassigning all the fields.
# If not, create a new Reference (Reference(**ref_obj)) object with data and add to session (session.add(ref))
# At the end of the full loop (or for each batch?), do session.commit()


def get_reference_batches(f):
    # Initialize empty batch of references
    reference_batch = []
    # Get all full batches
    for ref_no, reference in enumerate(f):
        reference_as_dict = json.loads(reference)
        reference_batch.append(reference_as_dict)
        if ref_no % BATCH_SIZE == (BATCH_SIZE-1):
            yield reference_batch
            reference_batch = []

    # Get partially filled batch
    if reference_batch.__len__():
        yield reference_batch


def import_references(filename, session):
    log.info("Importing references from %s" % filename)
    with open(filename) as f:
        for reference_batch in get_reference_batches(f):
            pmids = [ref['pubmed_id'] for ref in reference_batch]
            existing_references = session.query(assessment.Reference).\
                                  filter(assessment.Reference.pubmed_id in
                                         pmids).all()
            existing_pmids = [ref.pubmed_id for ref in existing_references]

            for reference in reference_batch:
                try:
                    index_of_existing_pmid = existing_pmids.index(reference['pubmed_id'])
                    existing_references[index_of_existing_pmid].update(**reference)
                except ValueError as e:
                    log.debug("Reference did not exist: %s" % e)
                    session.add(assessment.Reference(**reference))
            session.commit()

    log.info("References successfully imported!")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Deposit references from file")
    parser.add_argument('json_file', type=str,
                        help='relative path to file containing list of references')
    args = parser.parse_args()

    logging.basicConfig(level=logging.DEBUG)

    filename = os.path.abspath(args.json_file)
    # Import argparse, add CLI for getting path to JSON file.
    db = DB()
    db.connect()
    import_references(filename, db.session)
