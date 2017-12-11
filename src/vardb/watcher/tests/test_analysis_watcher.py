import os
import pytest
from vardb.deposit.deposit_from_vcf import DepositFromVCF
from vardb.datamodel.genotype import Genotype
from vardb.datamodel import DB
from vardb.datamodel import sample as sm
from vardb.watcher.analysis_watcher import *


non_existing_path = '123nonexistingpath'

watch_path = '/ella/src/vardb/watcher/testdata/analyses'
dest_path = '/ella/src/vardb/watcher/testdata/destination'

ready_data_path = '/ella/src/vardb/watcher/testdata/analyses/TestAnalysis-001'
empty_data_path = '/ella/src/vardb/watcher/testdata/analyses/TestAnalysis-002'

analysis_sample = 'TestAnalysis-001'
analysis_sample2 = 'TestAnalysis-002'

misconfigured_data_path = '/ella/src/vardb/watcher/testdata/analysis_with_error/TestAnalysis-003'
misconfigured_analysis_sample = 'TestAnalysis-003'


@pytest.fixture(scope='module')
def init_dest():
    os.system('rm -rf {}'.format(empty_data_path))
    os.system('rm -rf {}'.format(dest_path))
    os.mkdir(empty_data_path)
    os.mkdir(dest_path)
    yield 'dest_created'
    os.rmdir(dest_path)
    os.rmdir(empty_data_path)


def init(session, analysis_path=watch_path, destination_path=dest_path):
    aw = AnalysisWatcher(session, analysis_path, destination_path)
    return aw


def test_analysispath_throws_exception(session):
    with pytest.raises(RuntimeError) as excinfo:
        AnalysisWatcher(session, non_existing_path, '')
    assert watch_path_error.format(non_existing_path) in str(excinfo)

 
def test_destinationpath_throws_exception(session):
    with pytest.raises(RuntimeError) as excinfo:
        AnalysisWatcher(session, watch_path, non_existing_path)
    assert dest_path_error.format(non_existing_path) in str(excinfo) 

  
def test_ready_filepath(session, init_dest):
    aw = init(session)
    assert aw.is_ready(ready_data_path) == True
    assert aw.is_ready(empty_data_path) == False

  
def test_path_to_analysis_config(session, init_dest):
    aw = init(session)
    analysis_config_path = aw.path_to_analysis_config(ready_data_path, analysis_sample)
    # Name of .analysis file should match dir name
    #'/ella/src/vardb/watcher/testdata/analyses/TestAnalysis-001/TestAnalysis-001.analysis'
    assert analysis_config_path == ready_data_path + '/' + analysis_sample + analysis_postfix
  
    with pytest.raises(RuntimeError) as excinfo:
        aw.path_to_analysis_config(empty_data_path, analysis_sample) 
    
    expected_error = analysis_file_missing.format(empty_data_path + '/' + analysis_sample + analysis_postfix)
    assert expected_error  in str(excinfo)


def test_loading_config(session):
    aw = init(session)
    analysis_config_path = aw.path_to_analysis_config(ready_data_path, analysis_sample)
    analysis_config = aw.load_analysis_config(analysis_config_path)
    assert len(analysis_config['samples']) == 3
    assert analysis_config['priority'] == '1'
    assert analysis_config['name'] == analysis_sample


def test_loading_config_with_error(session):  
    aw = init(session)
    analysis_config_path = aw.path_to_analysis_config(misconfigured_data_path, misconfigured_analysis_sample)
    with pytest.raises(RuntimeError) as excinfo:
        aw.load_analysis_config(analysis_config_path)
    assert analysis_field_missing.format('priority', analysis_config_path) in str(excinfo)


def test_vcf_path(session, init_dest):
    aw = init(session)
    analysis_vcf_path = aw.path_to_vcf_file(ready_data_path, analysis_sample)
    assert analysis_vcf_path == ready_data_path + '/' + analysis_sample + vcf_postfix

    with pytest.raises(RuntimeError) as excinfo:
        aw.path_to_vcf_file(empty_data_path, analysis_sample)
    
    expected_error = vcf_file_missing.format(empty_data_path + '/' + analysis_sample + vcf_postfix)  
    assert expected_error in str(excinfo)


def test_extract_from_config(session):
    aw = init(session)
    analysis_config_data = aw.extract_from_config(ready_data_path, analysis_sample)
    assert analysis_config_data.analysis_name == analysis_sample
    assert analysis_config_data.gp_name == 'EEogPU'
    assert analysis_config_data.gp_version == 'v02'
    assert analysis_config_data.vcf_path == ready_data_path + '/' + analysis_sample + vcf_postfix


def test_extract_from_config_with_error(session, init_dest):
  aw = init(session)
  with pytest.raises(Exception) as excinfo:
      aw.extract_from_config(misconfigured_data_path, misconfigured_analysis_sample)
  assert "Missing field priority" in str(excinfo)


def test_import_analysis(session, test_database):
    print 'testing database ...'
    test_database.refresh()
    aw = AnalysisWatcher(session, watch_path, dest_path)
    
    analysis_config_data = aw.extract_from_config(ready_data_path, analysis_sample)
    aw.import_analysis(analysis_config_data)

    session.commit()

    with pytest.raises(RuntimeError) as excinfo:
         aw.import_analysis(analysis_config_data)

    assert 'Analysis TestAnalysis-001 is already imported.' in str(excinfo)

    db_genepanel = DepositFromVCF(session).get_genepanel(analysis_config_data.gp_name, analysis_config_data.gp_version)

    analysis_stored = session.query(sm.Analysis).filter(
        sm.Analysis.name == analysis_config_data.analysis_name,
        sm.Analysis.genepanel == db_genepanel
    ).all()

    assert len(analysis_stored) == 1