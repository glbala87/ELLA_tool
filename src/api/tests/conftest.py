import os
import re
import subprocess
import tempfile
import pytest
from sqlalchemy.pool import NullPool
from vardb.deposit.deposit_testdata import DepositTestdata
from vardb.util import DB
from api.rest_query import RestQuery
from api import db
from util import FlaskClientProxy

class TestDatabase(object):

    def __init__(self):
        self.dump_path = self.get_dump_path()

        # Reconnect with NullPool in order to avoid hanging connections
        # which prevents us from dropping/creating database
        db.connect(engine_kwargs={"poolclass": NullPool}, query_cls=RestQuery)

        if "@" in os.environ["DB_URL"]:
            self.host = re.findall(".*@([^/]*).*", os.environ["DB_URL"])[0]
        else:
            self.host = "localhost"

        self.create_dump()

    def get_dump_path(self):
        with tempfile.NamedTemporaryFile(delete=False) as tmpfile:
            return tmpfile.name

    def create_dump(self):
        """
        Creates a dump of the test database into file specified in self.dump_path.
        """
        with open(os.devnull, "w") as f:
            subprocess.call('createdb --host={host} vardb-test'.format(host=self.host), shell=True, stdout=f)
        DepositTestdata(db).deposit_all(test_set='integration_testing')
        subprocess.check_call('pg_dumpall --host={host} --file={path} --clean'.format(host=self.host, path=self.dump_path), shell=True)
        print "Temporary database file created at {}.".format(self.dump_path)

    def refresh(self):
        """
        Wipes out whole database, and recreates a clean copy from the dump.
        """
        print "Refreshing database with data from dump"
        with open(os.devnull, "w") as f:
            subprocess.check_call('psql --host={host} -d postgres < {path}'.format(host=self.host, path=self.dump_path), shell=True, stdout=f)

    def cleanup(self):
        print "Removing database"
        subprocess.call('dropdb --host={host} vardb-test'.format(host=self.host), shell=True)
        try:
            os.remove(self.dump_path)
            print "Temporary database file removed."
        except Exception:
            pass

@pytest.yield_fixture
def session(request):
    db = DB()
    db.connect()
    session = db.session()
    yield session
    # Close session on teardown
    session.close()
    db.disconnect()


# Will be shared among all tests
@pytest.yield_fixture(scope="session", autouse=True)
def test_database(request):
    """
    Fixture for creating a test database from test data set.
    When initialized, it deposits the data and creates a dump into a
    temporary file.
    The TestDatabase object is yielded in order for the user to
    be able to call refresh() when he wants a fresh database.
    """
    test_db = TestDatabase()
    yield test_db

    # Cleanup database on teardown
    test_db.cleanup()

@pytest.fixture
def client():
    """
    Fixture for a flask client proxy, that supports get, post etc.
    """
    return FlaskClientProxy()

