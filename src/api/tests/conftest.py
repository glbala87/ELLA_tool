
import pytest
from util import FlaskClientProxy
from vardb.util.testdatabase import TestDatabase
from vardb.util import DB


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
