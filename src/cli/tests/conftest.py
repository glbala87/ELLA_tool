import pytest
from vardb.util import DB
from click.testing import CliRunner
from cli.main import cli_group


# Sessions/connections are not closed after cli-call. Add this explicit disconnect here to remedy this.
def db_del(*args, **kwargs):
    try:
        args[0].disconnect()
    except:
        pass


DB.__del__ = db_del


@pytest.fixture
def run_command():
    runner = CliRunner()
    return lambda *args, **kwargs: runner.invoke(cli_group, *args, **kwargs)
