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
from typing import Set, List, Pattern
import logging
import json
import shutil
import argparse
import time
import re
import os
from pathlib import Path
from vardb.datamodel import DB
from vardb.deposit.deposit_analysis import DepositAnalysis
from vardb.deposit.analysis_config import AnalysisConfigData

log = logging.getLogger(__name__)
POLL_INTERVAL = 30

WATCH_PATH_ERROR = "Couldn't read from watch path {}, aborting..."
DEST_PATH_ERROR = "Couldn't write to destination path {}, aborting..."
ANALYSIS_FILE_MISSING = "Expected an analysis file at {}, but found none."
VCF_FILE_MISSING = "Expected a vcf file at {}, but found none."
ANALYSIS_FIELD_MISSING = "Missing field {} in analysis config at {}"
ANALYSIS_FILE_MISCONFIGURED = "The file {} is corrupt or JSON structure has missing values: {}"

REPORT_FILES = ["report.md", "report.txt"]
WARNINGS_FILES = ["warnings.md", "warnings.txt"]
ANALYSIS_POSTFIX = ".analysis"
VCF_POSTFIX = ".vcf"
PED_POSTFIX = ".ped"


class AnalysisWatcher(object):
    def __init__(self, session, watch_path, dest_path, whitelist=None):
        self.session = session
        self.watch_path = Path(watch_path)
        self.dest_path = Path(dest_path)
        self.whitelist: List[Pattern] = []
        if whitelist:
            for w in whitelist:
                log.info(f"Adding whitelist: {w}")
                self.whitelist.append(re.compile(w))
        self.processed: Set[str] = (
            set()
        )  # Keeping tracked of failed or ignored analyses to prevent log spamming

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

    def import_analysis(self, analysis_config_data):
        """
        Imports the analysis (+ connected samples) into the database.

        Data is not committed to database, this must be done separately.

        : AnalysisConfigData
        """

        da = DepositAnalysis(self.session)
        da.import_vcf(analysis_config_data)

    def is_ready(self, analysis_path):
        ready_file_path = analysis_path / "READY"

        if not ready_file_path.exists():
            logging.info("Analysis {} not ready yet (missing READY file).".format(analysis_path))
            return False
        else:
            return True

    def check_and_import(self):
        """
        Poll for new samples to process.
        """

        # The path to the root folder is the analysis folder, i.e. for our testdata
        # src/vardb/watcher/testdata/analyses, the target folder for analysis will be
        # the analysis folder
        for analysis_dir in sorted(self.watch_path.iterdir()):

            if analysis_dir in self.processed:
                continue

            try:
                analysis_path = self.watch_path / analysis_dir
                if not analysis_path.is_dir():
                    continue

                if not self.is_ready(analysis_path):
                    continue

                analysis_config_data = AnalysisConfigData(analysis_path)

                if self.whitelist:
                    if not any(i.match(analysis_config_data["name"]) for i in self.whitelist):
                        log.warning(
                            f"{analysis_config_data['name']} does not match any of the provided whitelists, ignoring..."
                        )
                        self.processed.add(analysis_dir)
                        continue

                # Import analysis
                self.import_analysis(analysis_config_data)

                # Flushing to check for errors in data, before moving files
                self.session.flush()

                # Move analysis dir to destination path.
                shutil.move(str(analysis_path), str(self.dest_path))

                # All is apparantly good, let's commit!
                self.session.commit()
                log.info("Analysis {} successfully imported!".format(analysis_config_data["name"]))

            # Catch all exceptions and carry on, otherwise one bad analysis can block all of them
            except Exception:
                log.exception("An exception occured while importing a new analysis. Skipping...")
                self.session.rollback()
                self.processed.add(analysis_dir)


def start_polling(session, analyses_path, destination_path, whitelist=None):
    aw = AnalysisWatcher(session, analyses_path, destination_path, whitelist=whitelist)
    while True:
        aw.check_and_import()
        time.sleep(POLL_INTERVAL)


if __name__ == "__main__":

    from applogger import setup_logger

    setup_logger()

    parser = argparse.ArgumentParser(
        description="Watch a folder for new analyses to import into database."
    )
    parser.add_argument(
        "--analyses", dest="analyses_path", required=True, help="Path to watch for new analyses"
    )
    parser.add_argument(
        "--dest",
        dest="dest",
        required=True,
        help="Destination path into which the processed data will be copied.",
    )
    parser.add_argument(
        "--whitelist",
        dest="whitelist",
        required=False,
        nargs="+",
        help="Regex expressions for whitelist of analysis names to import (multiple expressions supported)",
    )

    args = parser.parse_args()

    log.info("Polling for new analyses every: {} seconds".format(POLL_INTERVAL))

    db = DB()
    db.connect()
    start_polling(db.session, args.analyses_path, args.dest, whitelist=args.whitelist)
