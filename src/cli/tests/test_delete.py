import pytest
from vardb.datamodel import sample

REFRESHED = False


@pytest.mark.parametrize("analysis_id", [1, 2, 3, 4])
def test_analysis_delete(session, test_database, run_command, analysis_id):
    # Need to refresh once for this test
    global REFRESHED
    if not REFRESHED:
        test_database.refresh()
        REFRESHED = True

    result = run_command(["delete", "analysis", str(analysis_id)], input="Some reason\ny\n")
    assert result.exit_code == 0
    a = session.query(sample.Analysis).filter(sample.Analysis.id == analysis_id).first()

    assert a is None
