import pytest
from vardb.util.testdatabase import TestDatabase
from vardb.util import DB
from click.testing import CliRunner
from cli.cli import cli

# Sessions/connections are not closed after cli-call. Add this explicit disconnect here to remedy this.
DB.__del__ = lambda *args, **kwargs: args[0].disconnect()

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
def run_command():
    runner = CliRunner()
    return lambda *args, **kwargs: runner.invoke(cli, *args, **kwargs)

