# -*- coding: utf-8 -*-
"""
AnalysisWatcher

Watches a path for new analyses to import into database.

For one analysis that has three samples (e.g. a trio)
It expects the path structure to look like the following:


└── TestAnalysis-001
    ├── TestAnalysis-001.analysis
    ├── TestAnalysis-001.vcf
    ├── TestSample-001.bai
    ├── TestSample-001.bam
    ├── TestSample-001.sample
    ├── TestSample-002.bai
    ├── TestSample-002.bam
    ├── TestSample-002.sample
    ├── TestSample-003.bai
    ├── TestSample-003.bam
    └── TestSample-003.sample

The name of the root directory must match the name of the analysis file.
Furthermore, the name must also match the 'name' key within the .analysis json file.


"""

import os
import logging
import json
import shutil
import argparse
import time
from vardb.datamodel import DB
from vardb.deposit.deposit_analysis import DepositAnalysis

log = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)
POLL_INTERVAL = 5

watch_path_error = "Couldn't read from watch path {}, aborting..."
dest_path_error = "Couldn't write to destination path {}, aborting..."
analysis_file_missing = "Expected an analysis file at {}, but found none."
vcf_file_missing = "Expected a vcf file at {}, but found none."
analysis_file_misconfigured = "The file {} is corrupt or JSON structure has missing values: {}"

analysis_postfix = '.analysis'
vcf_postfix = '.vcf'
sample_postfix = '.sample'

class AnalysisWatcher(object):

    def __init__(self, session, watch_path, dest_path):
        self.session = session
        self.watch_path = watch_path
        self.dest_path = dest_path
        
        if not self._check_watch_path_readable():
          raise RuntimeError(watch_path_error.format(self.watch_path))

        if not self._check_dest_path_writable():
            raise RuntimeError(dest_path_error.format(self.dest_path))

    def _check_watch_path_readable(self):
        return os.access(self.watch_path, os.R_OK)

    def _check_dest_path_writable(self):
        return os.access(self.dest_path, os.W_OK)
      
    def load_analysis_config(self, analysis_config_path):
        with open(analysis_config_path) as f:
            analysis_config = json.load(f)
        self.check_analysis_config(analysis_config, analysis_config_path)
        return analysis_config

    def check_analysis_config(self, analysis_config, analysis_config_path):
        for field in ['name', 'samples']:
            if field not in analysis_config:
                raise RuntimeError("Missing field {} in analysis config at {}".format(field, analysis_config_path))

    def load_sample_config(self, sample_config_path):
        with open(sample_config_path) as f:
            sample_config = json.load(f)
        self.check_sample_config(sample_config, sample_config_path)
        return sample_config

    def check_sample_config(self, sample_config, sample_config_path):
        for field in ['name']:
            if field not in sample_config:
                raise RuntimeError("Missing field {} in sample config at {}".format(field, sample_config_path))

    def import_analysis(self, analysis_vcf_path, analysis_name, gp_name, gp_version):
        """
        Imports the analysis (+ connected samples) into the database.

        Data is not committed to database, this must be done separately.

        :param analysis_vcf_path: Path to vcf file
        :type analysis_vcf_path: str
        :param analysis_config: Preloaded analysis config
        :type analysis_config: dict
        :param sample_config: Preloaded sample configs
        :type sample_config: list
        """

        da = DepositAnalysis(self.session)
        
        da.import_vcf(
          path=analysis_vcf_path,
          analysis_name=analysis_name,
          gp_name=gp_name,
          gp_version=gp_version
          
        )

    def is_ready(self, analysis_path):
      
      ready_file_path = os.path.join(
        analysis_path,
        'READY'
      )
      
      if not os.path.exists(ready_file_path):
        logging.info("Analysis {} not ready yet (missing READY file).".format(analysis_path))
        return False
      else: 
        return True
      
    def path_to_analysis_config(self, analysis_path, analysis_dir):  
      # Name of .analysis file should match dir name
      analysis_config_path = os.path.join(
          analysis_path,
          analysis_dir + analysis_postfix
      )

      if not os.path.exists(analysis_config_path):
          raise RuntimeError(analysis_file_missing.format(analysis_config_path))

      return analysis_config_path

    def extract_sample_configs(self, analysis_config, analysis_dir):  
      sample_configs = list()
      # For each connected sample, load the relevant sample config and check them
      for sample_name in analysis_config['samples']:

          # Name of .sample file should match sample name
          sample_config_path = os.path.join(
              self.watch_path,
              analysis_dir,
              sample_name + sample_postfix
          )

          if not os.path.exists(sample_config_path):
              raise RuntimeError("Expected an sample file at {}, but found none.".format(sample_config_path))

          sample_configs.append(
              self.load_sample_config(sample_config_path)
          )
          
      return sample_configs
      
    def extract_from_config(self, analysis_path, analysis_dir):  
      analysis_file = self.path_to_analysis_config(analysis_path, analysis_dir)
      analysis_config   = self.load_analysis_config(analysis_file)
      sample_configs    = self.extract_sample_configs(analysis_config, analysis_dir)
      analysis_vcf_path = self.vcf_path(analysis_path, analysis_dir)
      
      try:
        gp = analysis_config['params']['genepanel']
        gp_name, gp_version = gp.split('_')
        analysis_name = analysis_config['name']
      
        if gp_name == '' or gp_version == '' or analysis_name == '':
          raise RuntimeError(analysis_file_misconfigured.format(
            analysis_file, ' gp_name: ' + gp_name + ' , gp_version: ' + gp_version + ' , analysis_name: ' + analysis_name
          ))
      
        return analysis_vcf_path, analysis_name, gp_name, gp_version, analysis_config
      
      except Exception:
        log.exception(analysis_file_misconfigured.format(analysis_path, ""))
      
    def vcf_path(self, analysis_path, analysis_dir):  
      # Check for a vcf file matching analysis name
      analysis_vcf_path = os.path.join(
          analysis_path,
          analysis_dir + vcf_postfix
      )

      # NB! Changing from sample_config_path in the old code, which seems to be a bug, to analysis_vcf_path
      if not os.path.exists(analysis_vcf_path):
          raise RuntimeError(vcf_file_missing.format(analysis_vcf_path))
      
      return analysis_vcf_path
      
    def check_and_import(self):
      """
        Poll for new samples to process.
        """
        
      # The path to the root folder is the analysis folder, i.e. for our testdata
      # src/vardb/watcher/testdata/analyses, the target folder for analysis will be 
      # the analysis folder
      for analysis_dir in os.listdir(self.watch_path):
        try:

          if not os.path.isdir(os.path.join(self.watch_path, analysis_dir)):
            continue

          analysis_path = os.path.join(
            self.watch_path,
            analysis_dir
          )

          if not self.is_ready(analysis_path):
            continue

          analysis_vcf_path, analysis_name, gp_name, gp_version, analysis_config  = self.extract_from_config(analysis_path, analysis_dir)

          # Import analysis
          self.import_analysis(
             analysis_vcf_path,
             analysis_name,
             gp_name,
             gp_version
          )

          self.session.flush()  
          # Move analysis dir to destination path.
          shutil.move(analysis_path, self.dest_path)

          # All is apparantly good, let's commit!
          self.session.commit()
          log.info("Analysis {} successfully imported!".format(analysis_config['name']))

        # Catch all exceptions and carry on, otherwise one bad analysis can block all of them
        except Exception:
          log.exception("An exception occured while import a new analysis. Skipping...")
          self.session.rollback()

def start_polling(session, analyses_path, destination_path):

    aw = AnalysisWatcher(session, analyses_path, destination_path)
    
    while True:
        try:
          aw.check_and_import()
        except Exception:
            log.exception("An exception occurred while checking for new genepanels.")

        time.sleep(POLL_INTERVAL)

if __name__ == '__main__':
  
    parser = argparse.ArgumentParser(description="Watch a folder for new analyses to import into database.")
    parser.add_argument("--analyses", dest="analyses_path", required=True,
                        help="Path to watch for new analyses")
    parser.add_argument("--dest", dest="dest", required=True,
                        help="Destination path into which the processed data will be copied.")
    
    args = parser.parse_args()

    log.info("Polling for new analyses every: {} seconds".format(POLL_INTERVAL))

    db = DB()
    db.connect()
  
    start_polling(db.session, args.analyses_path, args.dest)