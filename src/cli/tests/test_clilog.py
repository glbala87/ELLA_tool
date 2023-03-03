import datetime
import getpass
import sys

from vardb.datamodel import log


def test_clilog(test_database, session, run_command):
    test_database.refresh()

    result = run_command(["users", "reset_password", "testuser1"])
    assert result.exit_code == 0

    entry = session.query(log.CliLog).one()
    assert entry.user == getpass.getuser()
    assert (
        entry.output == "Reset password for user testuser1 (Ibsen, Henrik) with password *********"
    )
    assert entry.group == "users"
    assert entry.groupcommand == "reset_password"
    assert entry.reason is None
    assert entry.command == " ".join(sys.argv[1:])
    assert isinstance(entry.time, datetime.datetime)

    result = run_command(["delete", "analysis", "1"], input="Test reason\ny\n")
    assert result.exit_code == 0

    entry = session.query(log.CliLog).order_by(log.CliLog.id.desc()).first()
    assert entry.user == getpass.getuser()
    assert entry.output == "Analysis 1 (brca_decomposed.HBOC_v1.0.0) deleted successfully"
    assert entry.group == "delete"
    assert entry.groupcommand == "analysis"
    assert entry.reason == "Test reason"
    assert entry.command == " ".join(sys.argv[1:])
    assert isinstance(entry.time, datetime.datetime)
