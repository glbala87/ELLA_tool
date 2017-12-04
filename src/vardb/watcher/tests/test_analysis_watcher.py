
import os
import logging
import json
import shutil
import argparse
import time
import pytest
from vardb.watcher.analysis_watcher import *
from vardb.datamodel import DB

non_existing_path = '123nonexistingpath'
watch_path = '/ella/src/vardb/watcher/testdata/analyses'
dest_path = '/ella/src/vardb/watcher/testdata/destination'
ready_data_path = '/ella/src/vardb/watcher/testdata/analyses/TestAnalysis-001'
empty_data_path = '/ella/src/vardb/watcher/testdata/analyses/TestAnalysis-002'
analysis_sample = 'TestAnalysis-001'

def init_db():
  db = DB()
  db.connect()
  return db.session

@pytest.fixture(scope='module')
def init_dest():
  os.mkdir(dest_path)
  os.mkdir(empty_data_path)
  yield 'dest_created'
  os.rmdir(dest_path)
  os.rmdir(empty_data_path)
  

def init(analysisPath=watch_path, destinationPath=dest_path):
  aw = AnalysisWatcher(init_db(), analysisPath, destinationPath)
  return aw

def test_analysispath_throws_exception():
  with pytest.raises(RuntimeError) as excinfo:
    AnalysisWatcher(init_db(), non_existing_path, '')
  assert watch_path_error.format(non_existing_path) in str(excinfo)
 
def test_destinationpath_throws_exception():
  with pytest.raises(RuntimeError) as excinfo:
    AnalysisWatcher(init_db(), watch_path, non_existing_path)
  assert dest_path_error.format(non_existing_path) in str(excinfo) 
  
def test_ready_filepath(init_dest):
  aw = init()
  assert aw.is_ready(ready_data_path) == True
  assert aw.is_ready(empty_data_path) == False
  
def test_path_to_analysis_config(init_dest):
  aw = init()
  analysis_config_path = aw.path_to_analysis_config(ready_data_path, analysis_sample)
  # Name of .analysis file should match dir name
  #'/ella/src/vardb/watcher/testdata/analyses/TestAnalysis-001/TestAnalysis-001.analysis'
  assert analysis_config_path == ready_data_path + '/' + analysis_sample + analysis_postfix
  
  with pytest.raises(RuntimeError) as excinfo:
    aw.path_to_analysis_config(empty_data_path, analysis_sample) 
    
  expected_error = analysis_file_missing.format(empty_data_path + '/' + analysis_sample + analysis_postfix)
  assert expected_error  in str(excinfo)
  
def test_loading_config():
  aw = init()
  analysis_config_path = aw.path_to_analysis_config(ready_data_path, analysis_sample)
  analysis_config = aw.load_analysis_config(analysis_config_path)
  assert len(analysis_config['samples']) == 3
  
def test_extract_sample_configs():
  aw = init()
  analysis_config_path = aw.path_to_analysis_config(ready_data_path, analysis_sample)
  analysis_config = aw.load_analysis_config(analysis_config_path)
  sample_configs = aw.extract_sample_configs(analysis_config, ready_data_path)
  assert sample_configs[0]['name'] == 'TestSample-001'
  assert sample_configs[1]['name'] == 'TestSample-002'
  
def test_vcf_path(init_dest):
  aw = init()
  analysis_vcf_path = aw.vcf_path(ready_data_path, analysis_sample)
  assert analysis_vcf_path == ready_data_path + '/' + analysis_sample + vcf_postfix

  with pytest.raises(RuntimeError) as excinfo:
    aw.vcf_path(empty_data_path, analysis_sample)
    
  expected_error = vcf_file_missing.format(empty_data_path + '/' + analysis_sample + vcf_postfix)  
  assert expected_error in str(excinfo)

def test_import_analysis():
  aw = init()
  analysis_vcf_path, analysis_config, sample_configs = aw.setup_config(ready_data_path, analysis_sample)
  aw.import_analysis(analysis_vcf_path, analysis_config, sample_configs)
  
  1 == 1
