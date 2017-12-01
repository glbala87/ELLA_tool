
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

def init_db():
  db = DB()
  db.connect()
  return db.session

@pytest.fixture(scope='module')
def init_dest():
  os.mkdir(dest_path)
  yield 'dest_created'
  os.rmdir(dest_path)
  

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
  aw.check_and_import()
  assert 1 == 2