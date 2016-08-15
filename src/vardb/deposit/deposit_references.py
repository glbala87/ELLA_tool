import csv
import os
import logging
from vardb.datamodel import DB, allele, sample, assessment

SCRIPT_DIR = os.path.abspath(os.path.dirname(__file__))

REFERENCE_PATH = os.path.join(SCRIPT_DIR, '../testdata/references.csv')

log = logging.getLogger(__name__)

keys = [
    'id',
    'authors',
    'title',
    'journal',
    'year',
    'pubmed_id'
]


def import_references(engine):
    log.info("Importing references")
    with open(REFERENCE_PATH) as f:
        reader = csv.reader(f)

        # Avoid ORM for performance (not too much difference though)
        connection = engine.connect()
        trans = connection.begin()
        refs = list()
        for row in reader:
            del row[5]  # Remove URL
            refs.append({k: v for k, v in zip(keys, row)})
        try:
            connection.execute(
                assessment.Reference.__table__.insert(),
                refs
            )
            trans.commit()
        except Exception:
            trans.rollback()
            raise
    log.info("References successfully imported!")

if __name__ == '__main__':

    db = DB()
    db.connect()
    import_references(db.engine)
