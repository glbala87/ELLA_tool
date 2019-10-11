import os
import pytest
from vardb.deposit.deposit_from_vcf import DepositFromVCF
from vardb.datamodel import sample as sm
from vardb.watcher.analysis_watcher import (
    AnalysisWatcher,
    WATCH_PATH_ERROR,
    DEST_PATH_ERROR,
    ANALYSIS_POSTFIX,
    REPORT_FILES,
    WARNINGS_FILES,
    ANALYSIS_FILE_MISSING,
    VCF_POSTFIX,
    PED_POSTFIX,
    ANALYSIS_FIELD_MISSING,
    VCF_FILE_MISSING,
)


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


@pytest.fixture()
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
    assert aw.is_ready(ready_data_path) is True
    assert aw.is_ready(empty_data_path) is False


def test_path_to_analysis_config(session, init_dest):
    aw = init(session)
    analysis_config_path = aw.path_to_analysis_config(ready_data_path, analysis_sample)
    # Name of .analysis file should match dir name
    assert analysis_config_path == ready_data_path + "/" + analysis_sample + ANALYSIS_POSTFIX

    expected_error = ANALYSIS_FILE_MISSING.format(
        empty_data_path + "/" + analysis_sample + ANALYSIS_POSTFIX
    )

    with pytest.raises(RuntimeError, match=expected_error):
        aw.path_to_analysis_config(empty_data_path, analysis_sample)


def test_loading_report(session, init_dest):
    aw = init(session)
    report = aw.load_file(ready_data_path, REPORT_FILES[0])
    assert "Report" in str(report)


def test_loading_warnings(session, init_dest):
    aw = init(session)
    report = aw.load_file(ready_data_path, WARNINGS_FILES[0])
    assert "Warning" in str(report)


def test_loading_config(session, init_dest):
    aw = init(session)
    analysis_config_path = aw.path_to_analysis_config(ready_data_path, analysis_sample)
    analysis_config = aw.load_analysis_config(analysis_config_path)
    assert analysis_config["priority"] == "1"
    assert analysis_config["name"] == analysis_sample


def test_loading_config_with_error(session, init_dest):
    aw = init(session)
    analysis_config_path = aw.path_to_analysis_config(
        misconfigured_data_path, misconfigured_analysis_sample
    )

    with pytest.raises(
        RuntimeError, match=ANALYSIS_FIELD_MISSING.format("name", analysis_config_path)
    ):
        aw.load_analysis_config(analysis_config_path)


def test_vcf_path(session, init_dest):
    aw = init(session)
    analysis_vcf_path, analysis_ped_path = aw.path_to_vcf_file(ready_data_path, analysis_sample)
    assert analysis_vcf_path == os.path.join(ready_data_path, analysis_sample + VCF_POSTFIX)
    assert analysis_ped_path == os.path.join(ready_data_path, analysis_sample + PED_POSTFIX)

    expected_error = VCF_FILE_MISSING.format(empty_data_path + "/" + analysis_sample + VCF_POSTFIX)
    with pytest.raises(RuntimeError, match=expected_error):
        aw.path_to_vcf_file(empty_data_path, analysis_sample)


def test_extract_from_config(session, init_dest):
    aw = init(session)
    analysis_config_data = aw.extract_from_config(ready_data_path, analysis_sample)
    assert analysis_config_data.analysis_name == analysis_sample
    assert analysis_config_data.gp_name == "HBOC"
    assert analysis_config_data.gp_version == "v01"
    assert analysis_config_data.vcf_path == ready_data_path + "/" + analysis_sample + VCF_POSTFIX
    assert "Report" in str(analysis_config_data.report)
    assert "Warning" in str(analysis_config_data.warnings)


def test_extract_from_config_with_error(session, init_dest):
    aw = init(session)
    with pytest.raises(Exception, match="Missing field name"):
        aw.extract_from_config(misconfigured_data_path, misconfigured_analysis_sample)


def test_import_analysis(session, test_database, init_dest):
    test_database.refresh()
    aw = AnalysisWatcher(session, watch_path, dest_path)

    analysis_config_data = aw.extract_from_config(ready_data_path, analysis_sample)
    aw.import_analysis(analysis_config_data)

    session.commit()

    with pytest.raises(RuntimeError, match="Analysis TestAnalysis-001 is already imported."):
        aw.import_analysis(analysis_config_data)

    db_genepanel = DepositFromVCF(session).get_genepanel(
        analysis_config_data.gp_name, analysis_config_data.gp_version
    )

    analysis_stored = (
        session.query(sm.Analysis)
        .filter(
            sm.Analysis.name == analysis_config_data.analysis_name,
            sm.Analysis.genepanel == db_genepanel,
        )
        .all()
    )

    assert len(analysis_stored) == 1


def test_check_and_import(session, test_database, init_dest):
    aw = init(session)

    test_database.refresh()
    aw = AnalysisWatcher(session, watch_path, dest_path)

    analysis_config_data = aw.extract_from_config(ready_data_path, analysis_sample)

    aw.check_and_import()

    db_genepanel = DepositFromVCF(session).get_genepanel(
        analysis_config_data.gp_name, analysis_config_data.gp_version
    )

    analysis_stored = (
        session.query(sm.Analysis)
        .filter(
            sm.Analysis.name == analysis_config_data.analysis_name,
            sm.Analysis.genepanel == db_genepanel,
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
