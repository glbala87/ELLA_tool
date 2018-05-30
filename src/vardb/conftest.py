import pytest
from vardb.util.testdatabase import TestDatabase
from vardb.util import DB


@pytest.yield_fixture()
def session():
    db = DB()
    db.connect()
    session = db.session()

    yield session
    # Close session on teardown
    session.close()
    db.disconnect()

@pytest.yield_fixture(scope="module")
def session_module():
    db = DB()
    db.connect()
    session = db.session()

    yield session
    # Close session on teardown
    session.close()
    db.disconnect()



# Will be shared among all tests
@pytest.yield_fixture(scope="session", autouse=True)
def test_database():
    """
    The TestDatabase object is yielded in order for the user to
    be able to call refresh() when he wants a fresh database.
    """
    test_db = TestDatabase()
    test_db.refresh()
    yield test_db

    # Cleanup database on teardown
    test_db.cleanup()
