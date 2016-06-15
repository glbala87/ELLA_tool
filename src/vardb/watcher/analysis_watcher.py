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

from vardb.deposit.deposit import Importer

log = logging.getLogger(__name__)


class AnalysisWatcher(object):

    def __init__(self, session, watch_path, dest_path):
        self.session = session
        self.watch_path = watch_path
        self.dest_path = dest_path

        if not self._check_dest_path_writable():
            raise RuntimeError("Couldn't write to destination path {}, aborting...".format(self.dest_path))

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

    def import_analysis(self, analysis_vcf_path, analysis_config, sample_configs):
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

        importer = Importer(self.session)
        importer.importVcf(
            analysis_vcf_path,
            sample_configs=sample_configs,
            analysis_config=analysis_config,
            import_assessments=False
        )

    def check_and_import(self):
        """
        Poll for new samples to process.
        """

        for analysis_dir in os.listdir(self.watch_path):
            try:
                if not os.path.isdir(os.path.join(self.watch_path, analysis_dir)):
                    continue

                analysis_path = os.path.join(
                    self.watch_path,
                    analysis_dir
                )
                # Check for READY file
                ready_file_path = os.path.join(
                    analysis_path,
                    'READY'
                )
                if not os.path.exists(ready_file_path):
                    logging.info("Analysis {} not ready yet (missing READY file).".format(analysis_path))
                    continue

                # Name of .analysis file should match dir name
                analysis_config_path = os.path.join(
                    analysis_path,
                    analysis_dir + '.analysis'
                )
                if not os.path.exists(analysis_config_path):
                    raise RuntimeError("Expected an analysis file at {}, but found none.".format(analysis_config_path))

                # Load analysis config
                analysis_config = self.load_analysis_config(analysis_config_path)

                sample_configs = list()
                # For each connected sample, load the relevant sample config and check them
                for sample_name in analysis_config['samples']:

                    # Name of .sample file should match sample name
                    sample_config_path = os.path.join(
                        self.watch_path,
                        analysis_dir,
                        sample_name + '.sample'
                    )
                    if not os.path.exists(sample_config_path):
                        raise RuntimeError("Expected an sample file at {}, but found none.".format(sample_config_path))

                    sample_configs.append(
                        self.load_sample_config(sample_config_path)
                    )

                # Check for a vcf file matching analysis name
                analysis_vcf_path = os.path.join(
                    analysis_path,
                    analysis_dir + '.vcf'
                )

                if not os.path.exists(sample_config_path):
                    raise RuntimeError("Expected a vcf file at {}, but found none.".format(analysis_vcf_path))

                # Import analysis
                self.import_analysis(
                    analysis_vcf_path,
                    analysis_config,
                    sample_configs
                )

                # Move analysis dir to destination path.
                shutil.move(analysis_path, self.dest_path)

                # All is apparantly good, let's commit!
                self.session.commit()
                log.info("Analysis {} successfully imported!".format(analysis_config['name']))

            # Catch all exceptions and carry on, otherwise one bad analysis can block all of them
            except Exception:
                log.exception("An exception occured while import a new analysis. Skipping...")
                self.session.rollback()
