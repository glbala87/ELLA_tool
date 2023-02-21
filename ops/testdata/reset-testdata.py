#!/usr/bin/env python3
from __future__ import annotations

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
from typing import Any, Dict, List, Optional, Tuple, cast

import click
import requests
import yaml
from git import Repository
from sqlalchemy.engine import Engine
from sqlalchemy.orm import scoped_session

from api.config.config import feature_is_enabled
from cli.commands.database.make_db import make_db
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

logger = logging.getLogger(__file__)
logger.setLevel(logging.INFO)
logging.getLogger("git").setLevel(logging.INFO)
logging.getLogger("urllib3.connectionpool").setLevel(logging.WARNING)

ROOT = Path(__file__).absolute().parents[2]
TESTDATA_REPO_DIR = ROOT / "ella-testdata"
TESTDATA_SUBMODULE = ROOT / ".git" / "modules" / "ella-testdata"
TESTDATA_DIR = TESTDATA_REPO_DIR / "testdata"
GP_DIR = TESTDATA_DIR / "clinicalGenePanels"
FIXTURES_DIR = TESTDATA_DIR / "fixtures"
ANALYSES_DIR = TESTDATA_DIR / "analyses"
DB_URL = os.getenv("DB_URL", "postgresql:///postgres")

SPACES_CONFIG = {"bucket_name": "ella", "is_public": True, "region": "fra1"}
DUMP_URL_ROOT = "https://ella.fra1.digitaloceanspaces.com/testdata"
SPECIAL_TESTSET_SKIPPING_VCF = "empty"

###
### Find and load metadata for all available and versioned testsets
###


class Fixtures(Enum):
    USERS = FIXTURES_DIR / "users.json"
    USERGROUPS = FIXTURES_DIR / "usergroups.json"
    FILTERCONFIGS = FIXTURES_DIR / "filterconfigs.json"
    ANNOTATIONCONFIG = FIXTURES_DIR / "annotation-config.yml"
    REFERENCES = FIXTURES_DIR / "references.json"
    CUSTOM_ANNO = FIXTURES_DIR / "custom_annotation_test.json"


class DumpType(Enum):
    LOCAL = "local"
    WEB = "web"
    NONE = "none"

    def __str__(self) -> str:
        return self.value


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
            gp_item / f"{gp_item.name}_genes_transcripts_regions.tsv",
            gp_item / f"{gp_item.name}_phenotypes.tsv",
            *gp_item.name.split("_"),
        )
    )

ANALYSES: List[AnalysisInfo] = []
DEFAULT_TESTSET = "default"
for an_item in ANALYSES_DIR.iterdir():
    if not an_item.is_dir():
        continue
    ANALYSES.append(AnalysisInfo(an_item, an_item.name, an_item.name == DEFAULT_TESTSET))
AVAILABLE_TESTSETS = [SPECIAL_TESTSET_SKIPPING_VCF] + [a.name for a in ANALYSES]

# TODO: determine a way to not have this hard coded
ALLELES = [
    AlleleInfo(
        "analyses/default/brca_sample_1.HBOC_v1.0.0/brca_sample_1.HBOC_v1.0.0.vcf.gz",
        ("HBOC", "v1.0.0"),
    ),
]


###
### Classes
###


class Context:
    db: DB
    repo: Repository
    testset: str
    _web_dump: Optional[str] = None
    _local_dump: Optional[Path] = None
    _dump_type: Optional[DumpType] = None

    def __init__(self) -> None:
        self.repo = Repository(
            repo_dir=TESTDATA_REPO_DIR,
            # git_dir=TESTDATA_SUBMODULE if TESTDATA_SUBMODULE.exists() else None,
        )
        self.db = DB()
        self.db.connect()

    @property
    def dump_type(self) -> DumpType:
        if not self._dump_type:
            if self.repo.is_clean():
                if self.local_dump_exists():
                    self._dump_type = DumpType.LOCAL
                elif self.web_dump_exists():
                    self._dump_type = DumpType.WEB
                else:
                    self._dump_type = DumpType.NONE
            else:
                logger.warning(
                    "Found uncommitted changes in local testdata repo: not loading from db dump"
                )
                self._dump_type = DumpType.NONE
        return self._dump_type

    @property
    def dump_dir(self):
        dd = self.repo.repo_dir / "dumps"
        if self.repo.tag:
            dd /= str(self.repo.tag)
        elif self.repo.sha:
            dd /= str(self.repo.sha)
        else:
            raise ValueError(f"No tag or sha found in {self.repo.repo_dir}")
        return dd

    @property
    def web_dump(self):
        if self._web_dump is None:
            self._web_dump = f"{DUMP_URL_ROOT}/{self.repo.sha}/{self.local_dump.name}"
        return self._web_dump

    @property
    def local_dump(self):
        if self._local_dump is None:
            self._local_dump = self.dump_dir / f"ella-testdata-{self.testset}.psql.gz"
        return self._local_dump

    def has_dump(self):
        return self.dump_type is not DumpType.NONE

    def web_dump_exists(self):
        r = requests.head(self.web_dump)
        logger.debug(f"got {r.status_code} back when checking HEAD for {self.web_dump}")
        return r.status_code < 400

    def local_dump_exists(self):
        return self.local_dump.exists()

    def read_dump(self):
        if self.dump_type is DumpType.LOCAL:
            logger.info(f"Loading local dump {self.local_dump}")
            return self.local_dump.read_bytes()
        elif self.dump_type is DumpType.WEB:
            logger.info(f"Loading web dump {self.web_dump}")
            r = requests.get(self.web_dump)
            if r.status_code < 400:
                return r.content
            else:
                logger.error(f"got {r.status_code} when attempting to download {self.web_dump}")
                exit(1)
        else:
            logger.error(f"no dump found for {self.testset}")
            exit(1)


class CliActions(Enum):
    RESET = "reset"
    DUMP = "dump"
    UPLOAD = "upload"


class DepositTestdata:
    session: scoped_session
    engine: Engine

    ANALYSIS_FILE_RE = re.compile(
        r"(?P<analysis_name>.+\.(?P<genepanel_name>.+)_(?P<genepanel_version>.+))\.vcf.gz"
    )

    def __init__(self, db: DB):
        assert db.session and db.engine
        self.engine = cast(Engine, db.engine)
        self.session = db.session

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

    def deposit_analyses(self, test_set: str):
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
### Database functions
###


def drop_db(db: DB, remake: bool = False):
    db.engine.execute("DROP SCHEMA public CASCADE")
    db.engine.execute("CREATE SCHEMA public")

    if remake:
        make_db(db)
        db.session.commit()

    db.disconnect()


def restore_db(db: DB, remake: bool = False):
    drop_db(db, remake=False)
    make_db(db)
    db.session.commit()
    db.disconnect()


def reset_from_dump(db: DB, data: bytes):
    drop_db(db, remake=False)

    p = subprocess.Popen(
        ["psql", DB_URL],
        stdin=subprocess.PIPE,
        stdout=Path(os.devnull).open("w"),
    )
    p.communicate(gzip.decompress(data))
    p.wait()


def reset(db: DB, test_set: str = "default"):
    logger.info("Resetting database from script")
    drop_db(db=db, remake=True)

    dt = DepositTestdata(db)
    dt.deposit_all(test_set)


###
### CLI
###


@click.group(invoke_without_command=True)
@click.option("--testset", hidden=True)
@click.pass_context
def cli(ctx: click.Context, testset: Optional[str]):
    # support reset as default command
    if ctx.invoked_subcommand is None:
        ctx.invoke(reset_db, testset=testset)  # type: ignore


@click.command("dump")
@click.option("--testset", required=True, help="Name for the new dataset")
@click.pass_obj
def dump_db(ctx: Context, testset: str):
    ctx.testset = testset

    ctx.dump_dir.mkdir(exist_ok=True, parents=True)
    if ctx.local_dump.exists():
        logger.warning(f"Overwriting existing local dump file for {ctx.testset}: {ctx.local_dump}")

    proc = subprocess.run(
        ["pg_dump", DB_URL],
        cwd=ctx.local_dump.parent,
        stdout=subprocess.PIPE,
    )
    ctx.local_dump.write_bytes(gzip.compress(proc.stdout))
    logger.info(f"Dumped database to {ctx.local_dump}")


@click.command("reset")
@click.option(
    "--testset",
    default=DEFAULT_TESTSET,
    show_default=True,
    help="Name of test set to use",
)
@click.pass_obj
def reset_db(ctx: Context, testset: str):
    ctx.testset = testset or DEFAULT_TESTSET

    if ctx.has_dump():
        logger.info(f"Restoring database {DB_URL} from {ctx.dump_type} dump")
        reset_from_dump(ctx.db, ctx.read_dump())
    elif ctx.testset not in AVAILABLE_TESTSETS:
        logger.error(f"Invalid or non-existent testset name: {ctx.testset}")
        exit(1)
    else:
        logger.info(f"Resetting {DB_URL} from legacy testset: {ctx.testset}")
        reset(ctx.db, ctx.testset)
    logger.info("Database reset")


@click.command("upload")
@click.option("--testset", required=True, help="Name of the dataset to upload")
@click.pass_obj
def upload_dump(ctx: Context, testset: str):
    ctx.testset = testset
    if not ctx.local_dump.exists():
        raise FileNotFoundError(f"No dump found for {testset}")

    print("\nrun manually:")
    print(
        f"awsdo s3 cp --acl public-read {ctx.local_dump.relative_to(ROOT)} s3://ella/testdata/{ctx.repo.sha}/{ctx.local_dump.name}"
    )
    print()

    print("NotImplementedError: Automated uploading of dumps is not yet implemented")
    exit(1)


###

cli.add_command(reset_db)
cli.add_command(dump_db)
cli.add_command(upload_dump)


if __name__ == "__main__":
    if not TESTDATA_DIR.is_dir():
        raise FileNotFoundError(f"No directory found at {TESTDATA_DIR}")
    cli(obj=Context())
