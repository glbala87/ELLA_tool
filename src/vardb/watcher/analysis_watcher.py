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
from vardb.datamodel.analysis_config import AnalysisConfigData

log = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)
POLL_INTERVAL = 30

WATCH_PATH_ERROR = "Couldn't read from watch path {}, aborting..."
DEST_PATH_ERROR = "Couldn't write to destination path {}, aborting..."
ANALYSIS_FILE_MISSING = "Expected an analysis file at {}, but found none."
VCF_FILE_MISSING = "Expected a vcf file at {}, but found none."
ANALYSIS_FIELD_MISSING = "Missing field {} in analysis config at {}"
ANALYSIS_FILE_MISCONFIGURED = "The file {} is corrupt or JSON structure has missing values: {}"

REPORT_FILES = ['report.md', 'report.txt']
WARNINGS_FILES = ['warnings.md', 'warnings.txt']
ANALYSIS_POSTFIX = '.analysis'
VCF_POSTFIX = '.vcf'


class AnalysisWatcher(object):

    def __init__(self, session, watch_path, dest_path):
        self.session = session
        self.watch_path = watch_path
        self.dest_path = dest_path

        if not self._check_watch_path_readable():
            raise RuntimeError(WATCH_PATH_ERROR.format(self.watch_path))

        if not self._check_dest_path_writable():
            raise RuntimeError(DEST_PATH_ERROR.format(self.dest_path))

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
        for field in ['name', 'params']:
            if field not in analysis_config:
                raise RuntimeError(ANALYSIS_FIELD_MISSING.format(field, analysis_config_path))

    def load_file(self, analysis_config_path, file_name):
        path_to_file = os.path.join(analysis_config_path, file_name)
        if os.path.isfile(path_to_file):
            with open(path_to_file) as f:
                return f.read()
        else:
            return None

    def import_analysis(self, analysis_config_data):
        """
        Imports the analysis (+ connected samples) into the database.

        Data is not committed to database, this must be done separately.

        : AnalysisConfigData
        """

        da = DepositAnalysis(self.session)
        da.import_vcf(analysis_config_data)

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
            analysis_dir + ANALYSIS_POSTFIX
        )

        if not os.path.exists(analysis_config_path):
            raise RuntimeError(ANALYSIS_FILE_MISSING.format(analysis_config_path))

        return analysis_config_path

    def path_to_vcf_file(self, analysis_path, analysis_dir):
        # Check for a vcf file matching analysis name
        analysis_vcf_path = os.path.join(
            analysis_path,
            analysis_dir + VCF_POSTFIX
        )

        # NB! Changing from sample_config_path in the old code, which seems to be a bug, to analysis_vcf_path
        if not os.path.exists(analysis_vcf_path):
            raise RuntimeError(VCF_FILE_MISSING.format(analysis_vcf_path))

        return analysis_vcf_path

    def extract_from_config(self, analysis_path, analysis_dir):
        analysis_file = self.path_to_analysis_config(analysis_path, analysis_dir)
        analysis_config = self.load_analysis_config(analysis_file)
        analysis_vcf_path = self.path_to_vcf_file(analysis_path, analysis_dir)

        try:
            gp = analysis_config['params']['genepanel']
            gp_name, gp_version = gp.split('_')
            analysis_name = analysis_config['name']
            priority = analysis_config.get('priority', 1)

            report = None
            warnings = None
            for report_file in REPORT_FILES:
                if report is None:
                    report = self.load_file(analysis_path, report_file)
            for warning_file in WARNINGS_FILES:
                if warnings is None:
                    warnings = self.load_file(analysis_path, warning_file)

            if gp_name == '' or gp_version == '':
                raise RuntimeError(ANALYSIS_FILE_MISCONFIGURED.format(
                    analysis_file, ' gp_name: ' + gp_name + ' , gp_version: ' + gp_version
                ))

            return AnalysisConfigData(analysis_vcf_path, analysis_name, gp_name, gp_version, priority, report, warnings)

        except Exception:
            log.exception(ANALYSIS_FILE_MISCONFIGURED.format(analysis_path, ""))

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

                analysis_config_data = self.extract_from_config(analysis_path, analysis_dir)

                # Import analysis
                self.import_analysis(analysis_config_data)

                # Flushing to check for errors in data, before moving files
                self.session.flush()

                # Move analysis dir to destination path.
                shutil.move(analysis_path, self.dest_path)

                # All is apparantly good, let's commit!
                self.session.commit()
                log.info("Analysis {} successfully imported!".format(analysis_config_data.analysis_name))

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
