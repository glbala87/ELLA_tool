import os
import pytest
import hypothesis as ht
from .util import FlaskClientProxy
from vardb.util.testdatabase import TestDatabase
from vardb.util import DB

ht.settings.register_profile("default")
ht.settings.register_profile("small", max_examples=20)
ht.settings.register_profile(
    "extensive",
    max_examples=3000,
    timeout=900,
    suppress_health_check=[ht.HealthCheck.hung_test],
    deadline=2000,
)
ht.settings.register_profile(
    "soak",
    max_examples=1000000,
    timeout=ht.unlimited,
    suppress_health_check=[ht.HealthCheck.hung_test],
    deadline=2000,
)

hypothesis_profile = os.environ.get("HYPOTHESIS_PROFILE", "default").lower()
ht.settings.load_profile(hypothesis_profile)


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
    test_db.refresh()
    yield test_db

    # Cleanup database on teardown
    test_db.cleanup()


@pytest.fixture
def client():
    """
    Fixture for a flask client proxy, that supports get, post etc.
    """
    return FlaskClientProxy()
