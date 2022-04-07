#!/usr/bin/env python3

import argparse
import datetime
import gzip
import json
import logging
import os
import re
import subprocess
import sys
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import requests
import yaml
from api.config.config import feature_is_enabled
from cli.commands.database.make_db import make_db
from sqlalchemy.orm import scoped_session
from sqlalchemy.engine import Engine
from vardb.deposit.annotation_config import deposit_annotationconfig
from vardb.deposit.deposit_alleles import DepositAlleles
from vardb.deposit.deposit_analysis import DepositAnalysis
from vardb.deposit.deposit_custom_annotations import import_custom_annotations
from vardb.deposit.deposit_filterconfigs import deposit_filterconfigs
from vardb.deposit.deposit_genepanel import DepositGenepanel
from vardb.deposit.deposit_references import import_references
from vardb.deposit.deposit_users import import_groups, import_users
from vardb.util.db import DB
from vardb.watcher.analysis_watcher import AnalysisConfigData

from git import Repository

logger = logging.getLogger(__file__)

ROOT = Path(__file__).absolute().parents[2]
TESTDATA_REPO_DIR = ROOT / "ella-testdata"
TESTDATA_DIR = TESTDATA_REPO_DIR / "testdata"
GP_DIR = TESTDATA_DIR / "clinicalGenePanels"
FIXTURES_DIR = TESTDATA_DIR / "fixtures"
ANALYSES_DIR = TESTDATA_DIR / "analyses"

SPACES_CONFIG = {"bucket_name": "ella", "is_public": True, "region": "fra1"}
SPECIAL_TESTSET_SKIPPING_VCF = "empty"

###
### deposit_testdata.py
###


class Args(argparse.Namespace):
    testset: Optional[str]


class Fixtures(Enum):
    USERS = FIXTURES_DIR / "users.json"
    USERGROUPS = FIXTURES_DIR / "usergroups.json"
    FILTERCONFIGS = FIXTURES_DIR / "filterconfigs.json"
    ANNOTATIONCONFIG = FIXTURES_DIR / "annotation-config.yml"
    REFERENCES = FIXTURES_DIR / "references.json"
    CUSTOM_ANNO = FIXTURES_DIR / "custom_annotation_test.json"


@dataclass(frozen=True)
class AnalysisInfo:
    path: Path
    name: str
    is_default: bool = False


@dataclass(frozen=True)
class GenepanelInfo:
    transcripts: Path
    phenotypes: Path
    name: str
    version: str


@dataclass(frozen=True)
class AlleleInfo:
    path: str
    genepanel: Tuple[str, str]


REPORT_EXAMPLE = TESTDATA_DIR / "example_report"
WARNINGS_EXAMPLE = TESTDATA_DIR / "example_warning"
GENEPANELS: List[GenepanelInfo] = []
for gp_item in GP_DIR.iterdir():
    if not gp_item.is_dir():
        continue
    GENEPANELS.append(
        GenepanelInfo(
            gp_item / f"{gp_item.name}.transcripts.csv",
            gp_item / f"{gp_item.name}.phenotypes.csv",
            *gp_item.name.split("_"),
        )
    )

ANALYSES: List[AnalysisInfo] = []
DEFAULT_TESTSET = "default"
for an_item in ANALYSES_DIR.iterdir():
    if not an_item.is_dir():
        continue
    ANALYSES.append(AnalysisInfo(an_item, an_item.name, an_item.name == DEFAULT_TESTSET))
AVAILABLE_TESTSETS: List[str] = [SPECIAL_TESTSET_SKIPPING_VCF] + [a.name for a in ANALYSES]

# TODO: determine a way to not have this hard coded
ALLELES = [
    AlleleInfo(
        "analyses/default/brca_sample_1.HBOC_v01/brca_sample_1.HBOC_v01.vcf.gz",
        ("HBOC", "v01"),
    ),
]


class DepositTestdata(object):
    session: scoped_session
    engine: Engine

    ANALYSIS_FILE_RE = re.compile(
        r"(?P<analysis_name>.+\.(?P<genepanel_name>.+)_(?P<genepanel_version>.+))\.vcf.gz"
    )

    def __init__(self, db: DB):
        assert db.session and db.engine
        self.engine = db.engine
        self.session = db.session
        self._genepanels = None
        self._analyses = None
        self._alleles = None

    @property
    def genepanels(self):
        if not self._genepanels:
            ...

        return self._genepanels

    @property
    def analyses(self):
        if not self._analyses:
            ...

        return self._analyses

    @property
    def alleles(self):
        if not self._alleles:
            ...

        return self._alleles

    def deposit_users(self):
        import_groups(self.session, json.loads(Fixtures.USERGROUPS.value.read_text()))
        import_users(self.session, json.loads(Fixtures.USERS.value.read_text()))

    def deposit_filter_configs(self):
        filter_configs = json.loads(Fixtures.FILTERCONFIGS.value.read_text())
        deposit_filterconfigs(self.session, filter_configs)
        logger.info("Added {} filter configs".format(len(filter_configs)))

    def deposit_annotation_config(self):
        annotation_config: Dict[str, Any] = yaml.safe_load(
            Fixtures.ANNOTATIONCONFIG.value.read_text()
        )
        deposit_annotationconfig(self.session, annotation_config)
        logger.info("Added annotation config")

    def deposit_analyses(self, test_set=None):
        """
        :param test_set: Which set to import.
        """

        if test_set is None:
            testset = next(v for v in ANALYSES if v.is_default)
        else:
            testset = next(v for v in ANALYSES if v.name == test_set)

        testset_path = TESTDATA_DIR / testset.path
        analysis_paths = [d for d in testset_path.iterdir() if d.is_dir()]
        analysis_paths.sort()

        for analysis_path in analysis_paths:
            analysis_files = [f for f in analysis_path.iterdir() if f.name.endswith(".analysis")]
            if len(analysis_files) > 1:
                if feature_is_enabled("cnv"):
                    analysis_file = next(
                        f for f in analysis_files if f.name.endswith("cnv.analysis")
                    )
                else:
                    analysis_file = next(
                        f for f in analysis_files if not f.name.endswith("cnv.analysis")
                    )
                config_path = analysis_file
            else:
                config_path = analysis_path

            try:
                acd = AnalysisConfigData(config_path)
                acd["warnings"] = (
                    WARNINGS_EXAMPLE.read_text() if acd["genepanel_name"] == "HBOC" else None
                )
                acd["report"] = REPORT_EXAMPLE.read_text()
                acd["date_requested"] = datetime.datetime.now().strftime("%Y-%m-%d")

                da = DepositAnalysis(self.session)
                da.import_vcf(acd)

                logger.info("Deposited {} as analysis".format(acd["name"]))
                self.session.commit()

            except UserWarning as e:
                logger.exception(str(e))
                sys.exit()

    def deposit_alleles(self):
        for allele in ALLELES:
            vcf_path = TESTDATA_DIR / allele.path

            da = DepositAlleles(self.session)
            da.import_vcf(vcf_path, allele.genepanel[0], allele.genepanel[1])
            logger.info("Deposited {} as single alleles".format(vcf_path))
            self.session.commit()

    def deposit_genepanels(self):
        dg = DepositGenepanel(self.session)
        for gpdata in GENEPANELS:
            dg.add_genepanel(
                gpdata.transcripts,
                gpdata.phenotypes,
                gpdata.name,
                gpdata.version,
                replace=False,
            )

    def deposit_all(self, test_set: str):
        if test_set not in AVAILABLE_TESTSETS:
            raise RuntimeError(
                "Test set {} not part of available test sets: {}".format(
                    test_set, ",".join(AVAILABLE_TESTSETS)
                )
            )

        logger.info("--------------------")
        logger.info("Starting a DB reset")
        logger.info("on {}".format(os.getenv("DB_URL", "DB_URL NOT SET, BAD")))
        logger.info("--------------------")
        self.deposit_annotation_config()
        self.deposit_genepanels()
        self.deposit_users()
        self.deposit_filter_configs()
        import_references(self.session, Fixtures.REFERENCES.value)
        if test_set in [SPECIAL_TESTSET_SKIPPING_VCF.upper(), SPECIAL_TESTSET_SKIPPING_VCF.lower()]:
            logger.info("Skipping deposit of vcf and custom annotations")
        else:
            self.deposit_analyses(test_set=test_set)
            self.deposit_alleles()
            import_custom_annotations(self.session, Fixtures.CUSTOM_ANNO.value)

        logger.info("--------------------")
        logger.info(" DB Reset Complete!")
        logger.info("--------------------")


###


def dump_exists(url: str):
    r = requests.head(url)
    logger.info(f"got {r.status_code} back when checking HEAD for {url}")
    return r.status_code < 400


def drop_db(db: DB, remake: bool = False):
    db.engine.execute("DROP SCHEMA public CASCADE")  # type: ignore
    db.engine.execute("CREATE SCHEMA public")  # type: ignore

    if remake:
        make_db(db)
        db.session.commit()  # type: ignore

    db.disconnect()


def reset_from_dump(db: DB, url: str):
    drop_db(db, remake=False)

    with requests.get(url) as r:
        p = subprocess.Popen(
            "psql -d postgres".split(), stdin=subprocess.PIPE, stdout=Path(os.devnull).open("w")
        )
        p.communicate(gzip.decompress(r.content))
        p.wait()


def reset(db: DB, test_set: str = "default"):
    logger.info(f"Resetting database from script")
    drop_db(db=db, remake=True)

    dt = DepositTestdata(db)
    dt.deposit_all(test_set)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--testset", help="Name of testset to import (legacy)")
    args = parser.parse_args(namespace=Args)

    repo = Repository(repo_dir=TESTDATA_REPO_DIR)
    archive_url = (
        "https://ella.fra1.digitaloceanspaces.com/testdata/"
        f"{repo.sha}/{args.testset or DEFAULT_TESTSET}/ella-testdata.psql.gz"
    )

    db = DB()
    db.connect()
    if dump_exists(archive_url):
        logger.info(f"Resetting database from dump {archive_url}")
        reset_from_dump(db, archive_url)
    elif args.testset:
        logger.info(f"Resetting from given testset: {args.testset}")
        reset(db, args.testset)
    else:
        logger.info(f"No dump available, loading default dataset")
        reset(db)
    logger.info("Database reset")


if __name__ == "__main__":
    main()
