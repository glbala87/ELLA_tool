import pytest
from vardb.datamodel import sample

@pytest.mark.parametrize("analysis_id", [1,2,3,4])
def test_analysis_delete(session, run_command, analysis_id):
    result = run_command(["analyses", "delete", str(analysis_id)], input="y\n")
    assert result.exit_code == 0
    a = session.query(
        sample.Analysis
    ).filter(
        sample.Analysis.id == analysis_id
    ).first()

    assert a is None
