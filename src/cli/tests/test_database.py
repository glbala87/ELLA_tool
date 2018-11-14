import pytest
from sqlalchemy.exc import ProgrammingError
from vardb.datamodel import annotationshadow


def test_database_refresh(session, run_command):
    session.execute("DROP TABLE IF EXISTS annotationshadowtranscript")
    session.execute("DROP TABLE IF EXISTS annotationshadowfrequency")

    session.commit()

    result = run_command(["database", "refresh", "-f"])
    assert result.exit_code == 0

    assert session.query(annotationshadow.AnnotationShadowFrequency).count() > 0
    assert session.query(annotationshadow.AnnotationShadowTranscript).count() > 0
