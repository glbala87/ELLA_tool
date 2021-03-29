import os
import pytest
from sqlalchemy import tuple_
from pathlib import Path
from vardb.deposit.analysis_config import AnalysisConfigData
from vardb.datamodel import sample as sm
from vardb.watcher.analysis_watcher import AnalysisWatcher, WATCH_PATH_ERROR, DEST_PATH_ERROR


non_existing_path = "123nonexistingpath"

watch_path = "/tmp/test-ella-watcher-analyses"
dest_path = "/tmp/test-ella-watcher-destination"

ready_data_source_path = "/ella/src/vardb/watcher/testdata/analyses/TestAnalysis-001"
ready_data_path = os.path.join(watch_path, "TestAnalysis-001")
empty_data_path = os.path.join(watch_path, "TestAnalysis-002")

analysis_sample = "TestAnalysis-001"
analysis_sample2 = "TestAnalysis-002"

misconfigured_data_path = "/ella/src/vardb/watcher/testdata/analysis_with_error/TestAnalysis-003"
misconfigured_analysis_sample = "TestAnalysis-003"


@pytest.fixture(scope="function", autouse=True)
def init_dest():
    print("cleaning up paths ..")
    os.system("rm -rf {}".format(empty_data_path))
    os.system("rm -rf {}".format(dest_path))
    os.system("rm -rf {}".format(watch_path))
    os.mkdir(watch_path)
    os.mkdir(dest_path)
    os.mkdir(empty_data_path)

    os.system("cp -r {} {}".format(ready_data_source_path, ready_data_path))

    print("paths are ready ..")
    os.system("touch {}/READY".format(ready_data_path))
    yield "dest_created"
    os.system("rm -rf {}".format(empty_data_path))
    os.system("rm -rf {}".format(dest_path))


def init(session, analysis_path=watch_path, destination_path=dest_path):
    aw = AnalysisWatcher(session, analysis_path, destination_path)
    return aw


def test_analysispath_throws_exception(session):
    with pytest.raises(RuntimeError, match=WATCH_PATH_ERROR.format(non_existing_path)):
        AnalysisWatcher(session, non_existing_path, "")


def test_destinationpath_throws_exception(session, init_dest):
    with pytest.raises(RuntimeError, match=DEST_PATH_ERROR.format(non_existing_path)):
        AnalysisWatcher(session, watch_path, non_existing_path)


def test_ready_filepath(session, init_dest):
    aw = init(session)
    assert aw.is_ready(Path(ready_data_path)) is True
    assert aw.is_ready(Path(empty_data_path)) is False


def test_import_analysis(session, test_database, init_dest):
    test_database.refresh()
    aw = AnalysisWatcher(session, watch_path, dest_path)

    analysis_config_data = AnalysisConfigData(ready_data_path)
    aw.import_analysis(analysis_config_data)

    session.flush()

    with pytest.raises(RuntimeError, match="Analysis TestAnalysis-001 is already imported."):
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


def test_check_and_import(session, test_database, init_dest):
    aw = init(session)

    test_database.refresh()
    aw = AnalysisWatcher(session, watch_path, dest_path)

    analysis_config_data = AnalysisConfigData(ready_data_path)

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

    files = os.listdir(watch_path)
    assert len(files) == 1
    assert files == [analysis_sample2]

    os.system("rm -r {}".format(watch_path))

    assert "Report" in str(analysis_stored[0].report)
    assert "Warning" in str(analysis_stored[0].warnings)


def test_check_and_import_whitelist_include(session, test_database, init_dest):
    aw = init(session)

    test_database.refresh()
    aw = AnalysisWatcher(session, watch_path, dest_path, whitelist=[f"^{analysis_sample}$"])

    analysis_config_data = AnalysisConfigData(ready_data_path)

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

    files = os.listdir(watch_path)
    assert len(files) == 1
    assert files == [analysis_sample2]

    os.system("rm -r {}".format(watch_path))

    assert "Report" in str(analysis_stored[0].report)
    assert "Warning" in str(analysis_stored[0].warnings)


def test_check_and_import_blacklist_exclude(session, test_database, init_dest):
    aw = init(session)

    test_database.refresh()
    aw = AnalysisWatcher(session, watch_path, dest_path, blacklist=[f"^{analysis_sample}$"])

    analysis_config_data = AnalysisConfigData(ready_data_path)

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

    files = os.listdir(watch_path)
    assert len(files) == 2
    assert set(files) == set([analysis_sample, analysis_sample2])

    os.system("rm -r {}".format(watch_path))


def test_check_and_import_whitelist_exclude(session, test_database, init_dest):
    aw = init(session)

    test_database.refresh()
    aw = AnalysisWatcher(session, watch_path, dest_path, whitelist=["^NonExisting$"])

    analysis_config_data = AnalysisConfigData(ready_data_path)

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

    files = os.listdir(watch_path)
    assert len(files) == 2
    assert set(files) == set([analysis_sample, analysis_sample2])

    os.system("rm -r {}".format(watch_path))
