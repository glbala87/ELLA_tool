import os
import logging
import argparse
import json
from vardb.datamodel import DB, assessment

SCRIPT_DIR = os.path.abspath(os.path.dirname(__file__))
TEST_DATABASE = os.path.join(SCRIPT_DIR, '../testdata/references_test.json')
BATCH_SIZE = 10
log = logging.getLogger(__name__)


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


def import_references(session, filename=TEST_DATABASE):
    log.info("Importing references from %s" % filename)
    with open(filename) as f:
        for reference_batch in get_reference_batches(f):
            pmids = [ref['pubmed_id'] for ref in reference_batch]
            existing_references = session.query(assessment.Reference).\
                                  filter(assessment.Reference.pubmed_id.in_(pmids)).all()
            existing_pmids = [ref.pubmed_id for ref in existing_references]

            for reference in reference_batch:
                try:
                    pmid = reference['pubmed_id']
                    index_of_existing_pmid = existing_pmids.index(pmid)
                    existing_reference = existing_references[index_of_existing_pmid]
                    for key, value in reference.iteritems():
                        setattr(existing_reference, key, value)
                    # session.query(assessment.Reference).\
                    #     filter(assessment.Reference.pubmed_id == pmid)\
                    #     .update(reference)
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
    import_references(db.session, filename=filename)
