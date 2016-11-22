import os
import subprocess
import tempfile
import pytest
from sqlalchemy.pool import NullPool
from vardb.deposit.deposit_testdata import DepositTestdata
from api.rest_query import RestQuery
from api import db


class TestDatabase(object):

    def __init__(self):
        self.dump_path = self.get_dump_path()

        # Reconnect with NullPool in order to avoid hanging connections
        # which prevents us from dropping/creating database
        db.connect(engine_kwargs={"poolclass": NullPool}, query_cls=RestQuery)

        self.create_dump()

    def get_dump_path(self):
        with tempfile.NamedTemporaryFile(delete=False) as tmpfile:
            return tmpfile.name

    def create_dump(self):
        """
        Creates a dump of the test database into file specified in self.dump_path.
        """
        with open(os.devnull, "w") as f:
            subprocess.call('createdb vardb-test', shell=True, stdout=f)
        DepositTestdata(db).deposit_all(test_set='integration_testing')
        subprocess.check_call('pg_dumpall --file={path} --clean'.format(path=self.dump_path), shell=True)
        print "Temporary database file created at {}.".format(self.dump_path)

    def refresh(self):
        """
        Wipes out whole database, and recreates a clean copy from the dump.
        """
        print "Refreshing database with data from dump"
        with open(os.devnull, "w") as f:
            subprocess.check_call('psql -d postgres < {path}'.format(path=self.dump_path), shell=True, stdout=f)

    def cleanup(self):
        print "Removing database"
        subprocess.call('dropdb vardb-test', shell=True)
        try:
            os.remove(self.dump_path)
            print "Temporary database file removed."
        except Exception:
            pass


# Will be shared among all tests
@pytest.fixture(scope="session")
def test_database(request):
    """
    Fixture for creating a test database from test data set.
    When initialized, it deposits the data and creates a dump into a
    temporary file.
    The TestDatabase object is yielded in order for the user to
    be able to call refresh() when he wants a fresh database.
    """
    return TestDatabase()


# Pre-create dump before starting any tests (autouse flag)
@pytest.fixture(scope="session", autouse=True)
def test_database_create_dump(request, test_database):
    request.addfinalizer(test_database.cleanup)
