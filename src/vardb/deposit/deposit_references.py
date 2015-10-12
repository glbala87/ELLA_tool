import csv
import os
import logging
from vardb.datamodel import db, allele, sample, assessment

SCRIPT_DIR = os.path.abspath(os.path.dirname(__file__))

REFERENCE_PATH = os.path.join(SCRIPT_DIR, '../testdata/references.csv')

log = logging.getLogger(__name__)


def import_references_sql():
    conn = db.engine.connect()
    trans = conn.begin()
    result = conn.execute('COPY reference FROM \'{}\' WITH CSV HEADER'.format(REFERENCE_PATH))
    trans.commit()
    conn.close()


def import_references():
    session = db.sessionmaker()
    log.info("Importing references")
    with open(REFERENCE_PATH) as f:
        reader = csv.reader(f)
        for row in reader:
            ref = assessment.Reference(
                id=row[0],
                authors=row[1],
                title=row[2],
                journal=row[3],
                year=row[4],
                URL=row[5],
                pubmedID=row[6]
            )
            session.add(ref)
    session.commit()
    log.info("References successfully imported!")

if __name__ == '__main__':
    import_references()
