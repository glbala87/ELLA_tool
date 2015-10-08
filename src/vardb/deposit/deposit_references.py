import os
from vardb.datamodel import db

SCRIPT_DIR = os.path.abspath(os.path.dirname(__file__))

REFERENCE_PATH = os.path.join(SCRIPT_DIR, '../testdata/references.csv')


def import_references():
    print db.engine.execute('COPY reference FROM \'{}\' WITH CSV HEADER'.format(REFERENCE_PATH))


if __name__ == '__main__':
    import_references()
