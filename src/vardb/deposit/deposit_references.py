import csv
import os
import logging
from vardb.datamodel import allele, sample, assessment

SCRIPT_DIR = os.path.abspath(os.path.dirname(__file__))

REFERENCE_PATH = os.path.join(SCRIPT_DIR, '../testdata/references.csv')

log = logging.getLogger(__name__)


def import_references(session):
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
