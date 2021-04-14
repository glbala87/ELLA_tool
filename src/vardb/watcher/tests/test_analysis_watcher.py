from sqlalchemy import tuple_
import os
from pathlib import Path
import pytest
import shutil
import tempfile
from vardb.deposit.analysis_config import AnalysisConfigData
from vardb.datamodel import sample as sm
from vardb.watcher.analysis_watcher import AnalysisWatcher, WATCH_PATH_ERROR, DEST_PATH_ERROR

READY_DATA_SOURCE_PATH = "/ella/src/vardb/watcher/testdata/analyses/TestAnalysis-001"
MISCONFIGURED_DATA_SOURCE_PATH = (
    "/ella/src/vardb/watcher/testdata/analysis_with_error/TestAnalysis-003"
)


def ready_path(watch_path):
    return watch_path / Path(READY_DATA_SOURCE_PATH).name


def not_ready_path(watch_path):
    return watch_path / "TestAnalysis-002-not-ready"


def misconfigured_data_path(watch_path):
    return watch_path / Path(MISCONFIGURED_DATA_SOURCE_PATH).name


def assert_ready_moved_to_dest(watch_path, dest_path):
    "Check that the folder defined by ready_path(watch_path) is not in watch_path, but is in dest_path"
    watch_files = set(os.listdir(watch_path))
    dest_files = set(os.listdir(dest_path))
    assert ready_path(watch_path).name not in watch_files
    assert ready_path(watch_path).name in dest_files


@pytest.fixture(scope="function")
def watch_path():
    "Create temporary directory, and create folders/symlinks as a fresh watch directory"
    _watch_path = Path(tempfile.mkdtemp())
    os.symlink(READY_DATA_SOURCE_PATH, ready_path(_watch_path))
    os.mkdir(not_ready_path(_watch_path))
    os.symlink(MISCONFIGURED_DATA_SOURCE_PATH, misconfigured_data_path(_watch_path))

    yield _watch_path

    shutil.rmtree(_watch_path)


@pytest.fixture(scope="function")
def dest_path():
    "Create temporary directory as a fresh destinatation directory"
    _dest_path = Path(tempfile.mkdtemp())
    yield _dest_path
    shutil.rmtree(_dest_path)


def test_analysispath_throws_exception(session):
    with pytest.raises(RuntimeError, match=WATCH_PATH_ERROR.format("nonexisting")):
        AnalysisWatcher(session, "nonexisting", "")


def test_destinationpath_throws_exception(session, watch_path):
    with pytest.raises(RuntimeError, match=DEST_PATH_ERROR.format("nonexisting")):
        AnalysisWatcher(session, watch_path, "nonexisting")


def test_ready_filepath(session, watch_path, dest_path):
    aw = AnalysisWatcher(session, watch_path, dest_path)
    assert aw.is_ready(ready_path(watch_path)) is True
    assert aw.is_ready(not_ready_path(watch_path)) is False


def test_import_analysis(session, test_database, watch_path, dest_path):
    test_database.refresh()
    aw = AnalysisWatcher(session, watch_path, dest_path)

    analysis_config_data = AnalysisConfigData(ready_path(watch_path))
    aw.import_analysis(analysis_config_data)

    session.flush()

    with pytest.raises(
        RuntimeError, match=f"Analysis {analysis_config_data['name']} is already imported."
    ):
        aw.import_analysis(analysis_config_data)

    analysis_stored = (
        session.query(sm.Analysis)
        .filter(
            sm.Analysis.name == analysis_config_data["name"],
            tuple_(sm.Analysis.genepanel_name, sm.Analysis.genepanel_version)
            == (analysis_config_data["genepanel_name"], analysis_config_data["genepanel_version"]),
        )
        .all()
    )

    assert len(analysis_stored) == 1


def test_check_and_import(session, test_database, watch_path, dest_path):
    test_database.refresh()
    aw = AnalysisWatcher(session, watch_path, dest_path)

    analysis_config_data = AnalysisConfigData(ready_path(watch_path))

    aw.check_and_import()

    analysis_stored = (
        session.query(sm.Analysis)
        .filter(
            sm.Analysis.name == analysis_config_data["name"],
            tuple_(sm.Analysis.genepanel_name, sm.Analysis.genepanel_version)
            == (analysis_config_data["genepanel_name"], analysis_config_data["genepanel_version"]),
        )
        .all()
    )
    assert len(analysis_stored) == 1

    assert_ready_moved_to_dest(watch_path, dest_path)

    assert "Report" in str(analysis_stored[0].report)
    assert "Warning" in str(analysis_stored[0].warnings)


def test_check_and_import_whitelist_include(session, test_database, watch_path, dest_path):
    test_database.refresh()
    analysis_config_data = AnalysisConfigData(ready_path(watch_path))
    aw = AnalysisWatcher(
        session, watch_path, dest_path, whitelist=[f"^{analysis_config_data['name']}$"]
    )

    aw.check_and_import()

    analysis_stored = (
        session.query(sm.Analysis)
        .filter(
            sm.Analysis.name == analysis_config_data["name"],
            tuple_(sm.Analysis.genepanel_name, sm.Analysis.genepanel_version)
            == (analysis_config_data["genepanel_name"], analysis_config_data["genepanel_version"]),
        )
        .all()
    )

    assert len(analysis_stored) == 1
    assert_ready_moved_to_dest(watch_path, dest_path)
    assert "Report" in str(analysis_stored[0].report)
    assert "Warning" in str(analysis_stored[0].warnings)


def test_check_and_import_blacklist_exclude(session, test_database, watch_path, dest_path):
    test_database.refresh()
    analysis_config_data = AnalysisConfigData(ready_path(watch_path))
    aw = AnalysisWatcher(
        session, watch_path, dest_path, blacklist=[f"^{analysis_config_data['name']}$"]
    )

    aw.check_and_import()

    analysis_stored = (
        session.query(sm.Analysis)
        .filter(
            sm.Analysis.name == analysis_config_data["name"],
            tuple_(sm.Analysis.genepanel_name, sm.Analysis.genepanel_version)
            == (analysis_config_data["genepanel_name"], analysis_config_data["genepanel_version"]),
        )
        .all()
    )

    assert len(analysis_stored) == 0
    with pytest.raises(AssertionError):
        assert_ready_moved_to_dest(watch_path, dest_path)


def test_check_and_import_whitelist_exclude(session, test_database, watch_path, dest_path):
    test_database.refresh()
    aw = AnalysisWatcher(session, watch_path, dest_path, whitelist=["^NonExisting$"])

    analysis_config_data = AnalysisConfigData(ready_path(watch_path))

    aw.check_and_import()

    analysis_stored = (
        session.query(sm.Analysis)
        .filter(
            sm.Analysis.name == analysis_config_data["name"],
            tuple_(sm.Analysis.genepanel_name, sm.Analysis.genepanel_version)
            == (analysis_config_data["genepanel_name"], analysis_config_data["genepanel_version"]),
        )
        .all()
    )

    assert len(analysis_stored) == 0

    with pytest.raises(AssertionError):
        assert_ready_moved_to_dest(watch_path, dest_path)


def test_check_and_import_whitelistfile(session, test_database, watch_path, dest_path):
    with tempfile.NamedTemporaryFile(mode="wt") as wlf:
        wlf.write("^NonExisting$")
        wlf.flush()
        test_database.refresh()
        aw = AnalysisWatcher(session, watch_path, dest_path, whitelistfile=wlf.name)

        analysis_config_data = AnalysisConfigData(ready_path(watch_path))

        aw.check_and_import()

        analysis_stored = (
            session.query(sm.Analysis)
            .filter(
                sm.Analysis.name == analysis_config_data["name"],
                tuple_(sm.Analysis.genepanel_name, sm.Analysis.genepanel_version)
                == (
                    analysis_config_data["genepanel_name"],
                    analysis_config_data["genepanel_version"],
                ),
            )
            .all()
        )

        assert len(analysis_stored) == 0

        with pytest.raises(AssertionError):
            assert_ready_moved_to_dest(watch_path, dest_path)

        wlf.write(f"\n^{analysis_config_data['name']}$")
        wlf.flush()

        aw.check_and_import()

        analysis_stored = (
            session.query(sm.Analysis)
            .filter(
                sm.Analysis.name == analysis_config_data["name"],
                tuple_(sm.Analysis.genepanel_name, sm.Analysis.genepanel_version)
                == (
                    analysis_config_data["genepanel_name"],
                    analysis_config_data["genepanel_version"],
                ),
            )
            .all()
        )

        assert len(analysis_stored) == 1

        assert_ready_moved_to_dest(watch_path, dest_path)


def test_check_and_import_blacklistfile_include(session, test_database, watch_path, dest_path):
    with tempfile.NamedTemporaryFile(mode="wt") as blf:
        blf.write("^NonExisting$")
        blf.flush()
        test_database.refresh()
        aw = AnalysisWatcher(session, watch_path, dest_path, blacklistfile=blf.name)

        analysis_config_data = AnalysisConfigData(ready_path(watch_path))

        aw.check_and_import()

        analysis_stored = (
            session.query(sm.Analysis)
            .filter(
                sm.Analysis.name == analysis_config_data["name"],
                tuple_(sm.Analysis.genepanel_name, sm.Analysis.genepanel_version)
                == (
                    analysis_config_data["genepanel_name"],
                    analysis_config_data["genepanel_version"],
                ),
            )
            .all()
        )

        assert len(analysis_stored) == 1

        assert_ready_moved_to_dest(watch_path, dest_path)


def test_check_and_import_blacklistfile_exclude(session, test_database, watch_path, dest_path):
    with tempfile.NamedTemporaryFile(mode="wt") as blf:
        analysis_config_data = AnalysisConfigData(ready_path(watch_path))
        blf.write(f"^{analysis_config_data['name']}$")
        blf.flush()
        test_database.refresh()
        aw = AnalysisWatcher(session, watch_path, dest_path, blacklistfile=blf.name)

        aw.check_and_import()

        analysis_stored = (
            session.query(sm.Analysis)
            .filter(
                sm.Analysis.name == analysis_config_data["name"],
                tuple_(sm.Analysis.genepanel_name, sm.Analysis.genepanel_version)
                == (
                    analysis_config_data["genepanel_name"],
                    analysis_config_data["genepanel_version"],
                ),
            )
            .all()
        )

        assert len(analysis_stored) == 0
        with pytest.raises(AssertionError):
            assert_ready_moved_to_dest(watch_path, dest_path)
