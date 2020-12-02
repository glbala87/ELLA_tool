#!/usr/bin/env python
"""
Code for adding or modifying gene panels in varDB.
"""

import datetime
import json
import logging
import os
import re


import sys
from dataclasses import dataclass
from typing import List, Optional, Tuple

import yaml

from vardb.datamodel import DB
from vardb.deposit.annotation_config import deposit_annotationconfig
from vardb.deposit.deposit_alleles import DepositAlleles
from vardb.deposit.deposit_analysis import DepositAnalysis
from vardb.deposit.deposit_custom_annotations import import_custom_annotations
from vardb.deposit.deposit_filterconfigs import deposit_filterconfigs
from vardb.deposit.deposit_genepanel import DepositGenepanel
from vardb.deposit.deposit_references import import_references
from vardb.deposit.deposit_users import import_groups, import_users
from vardb.util import vcfiterator
from vardb.watcher.analysis_watcher import AnalysisConfigData

SPECIAL_TESTSET_SKIPPING_VCF = "empty"

logging.basicConfig(level=logging.DEBUG)

log = logging.getLogger(__name__)

SCRIPT_DIR = os.path.abspath(os.path.dirname(__file__))


@dataclass(frozen=True)
class AnalysisInfo:
    path: str
    name: str
    is_default: bool = False


@dataclass(frozen=True)
class GenepanelInfo:
    transcripts: str
    phenotypes: str
    name: str
    version: str


@dataclass(frozen=True)
class AlleleInfo:
    path: str
    genepanel: Tuple[str, str]


# Paths are relative to script dir.

FIXTURES = "../testdata/test-fixtures"
USERS = "../testdata/users.json"
USERGROUPS = "../testdata/usergroups.json"
FILTERCONFIGS = "../testdata/filterconfigs.json"
ANNOTATIONCONFIG = "../testdata/annotation-config.yml"

REPORT_EXAMPLE = """
### Gene list for genes having below 100% coverage:

|Gene|Transcript|Phenotype|Inheritance||Coverage<br> (% bp) (2)|
|---|---|---|---|---|---|
|MSH2|NM_000251.2|Colorectal cancer, hereditary nonpolyposis, type 1|AD|2869|99.9%|
|MSH6|NM_000179.2|Colorectal cancer, hereditary nonpolyposis, type 5|AD|4123|99.2%|
|PMS2|NM_000535.5|Colorectal cancer, hereditary nonpolyposis, type 4|AD|2649|98.6%|

(1) bp = basepair; + 4 bp = -2 og + 2 bp in intron region to cover conserved splice site (based on Refseqs from UCSC refGene table, March 2015, GRCh37/hg19)
(2) Percentage of region covered at least 40 times

### Regions covered by less than 40 reads
|Start position (HGVSg)|End position (HGVSg)|Gene|Transcript|Exon|x covered|
|---|---|---|---|---|---|
|chr2:g.47630540N>N|chr2:g.47630543N>N|MSH2|NM_000251.2|exon1|36|
|chr2:g.48010497N>N|chr2:g.48010531N>N|MSH6|NM_000179.2|exon1|13|
|chr7:g.6013138N>N|chr7:g.6013175N>N|PMS2|NM_000535.5|exon15|11|
"""

WARNINGS_EXAMPLE = """
2 regions have too low coverage
chr7:g.6013138N>N chr7:g.6013175N>N
chr2:g.48010497N>N chr2:g.48010531N>N
"""

GENEPANELS = [
    GenepanelInfo(
        "../testdata/clinicalGenePanels/Mendeliome_v01/Mendeliome_v01.transcripts.csv",
        "../testdata/clinicalGenePanels/Mendeliome_v01/Mendeliome_v01.phenotypes.csv",
        "Mendeliome",
        "v01",
    ),
    GenepanelInfo(
        "../testdata/clinicalGenePanels/HBOCUTV_v01/HBOCUTV_v01.transcripts.csv",
        "../testdata/clinicalGenePanels/HBOCUTV_v01/HBOCUTV_v01.phenotypes.csv",
        "HBOCUTV",
        "v01",
    ),
    GenepanelInfo(
        "../testdata/clinicalGenePanels/HBOC_v01/HBOC_v01.transcripts.csv",
        "../testdata/clinicalGenePanels/HBOC_v01/HBOC_v01.phenotypes.csv",
        "HBOC",
        "v01",
    ),
    GenepanelInfo(
        "../testdata/clinicalGenePanels/Ciliopati_v05/Ciliopati_v05.transcripts.csv",
        "../testdata/clinicalGenePanels/Ciliopati_v05/Ciliopati_v05.phenotypes.csv",
        "Ciliopati",
        "v05",
    ),
]


ANALYSES = [
    AnalysisInfo("../testdata/analyses/default", "default", True),
    AnalysisInfo("../testdata/analyses/e2e", "e2e"),
    AnalysisInfo("../testdata/analyses/integration_testing", "integration_testing"),
    AnalysisInfo("../testdata/analyses/custom", "custom"),
    AnalysisInfo("../testdata/analyses/sanger", "sanger"),
    AnalysisInfo("../testdata/analyses/sv/", "sv"),
]

ALLELES = [
    AlleleInfo(
        "../testdata/analyses/default/brca_sample_1.HBOC_v01/brca_sample_1.HBOC_v01.vcf",
        ("HBOC", "v01"),
    )
]


DEFAULT_TESTSET: str = next(filter(lambda a: a.is_default, ANALYSES)).name
AVAILABLE_TESTSETS: List[str] = [SPECIAL_TESTSET_SKIPPING_VCF] + [a.name for a in ANALYSES]

CNV_ALLELES = [
    {
        "path": "../testdata/sv-testdata/HG002_sv_cnv.Mendeliome_v01.vcf",
        "genepanel": ("Mendeliome", "v01"),
    }
]

REFERENCES = "../testdata/references_test.json"
CUSTOM_ANNO = "../testdata/custom_annotation_test.json"


class DepositTestdata(object):

    ANALYSIS_FILE_RE = re.compile(
        r"(?P<analysis_name>.+\.(?P<genepanel_name>.+)_(?P<genepanel_version>.+))\.vcf"
    )

    def __init__(self, db):
        self.engine = db.engine
        self.session = db.session

    def _get_vcf_samples(self, vcf_path):
        vi = vcfiterator.VcfIterator(vcf_path)
        return vi.getSamples()

    def deposit_users(self):
        with open(os.path.join(SCRIPT_DIR, USERGROUPS)) as f:
            import_groups(self.session, json.load(f))

        with open(os.path.join(SCRIPT_DIR, USERS)) as f:
            import_users(self.session, json.load(f))

    def deposit_filter_configs(self):

        with open(os.path.join(SCRIPT_DIR, FILTERCONFIGS)) as f:
            filter_configs = json.load(f)
            deposit_filterconfigs(self.session, filter_configs)
            log.info("Added {} filter configs".format(len(filter_configs)))

    def deposit_annotation_config(self):
        with open(os.path.join(SCRIPT_DIR, ANNOTATIONCONFIG)) as f:
            annotation_config = yaml.safe_load(f)
            deposit_annotationconfig(self.session, annotation_config)
            log.info("Added annotation config")

    def deposit_analyses(self, test_set=None):
        """
        :param test_set: Which set to import.
        """

        if test_set is None:
            testset = next(v for v in ANALYSES if v.is_default)
        else:
            testset = next(v for v in ANALYSES if v.name == test_set)

        testset_path = os.path.join(SCRIPT_DIR, testset.path)
        analysis_paths = [os.path.join(testset_path, d) for d in os.listdir(testset_path)]
        analysis_paths.sort()

        for analysis_path in analysis_paths:
            if not os.path.isdir(analysis_path):
                continue
            try:
                acd = AnalysisConfigData(analysis_path)
                acd["warnings"] = WARNINGS_EXAMPLE if acd["genepanel_name"] == "HBOC" else None
                acd["report"] = REPORT_EXAMPLE
                acd["date_requested"] = datetime.datetime.now().strftime("%Y-%m-%d")

                da = DepositAnalysis(self.session)
                da.import_vcf(acd)

                log.info("Deposited {} as analysis".format(acd["name"]))
                self.session.commit()

            except UserWarning as e:
                log.exception(str(e))
                sys.exit()

    def deposit_alleles(self):

        for allele in ALLELES:
            vcf_path = os.path.join(SCRIPT_DIR, allele.path)

            da = DepositAlleles(self.session)
            da.import_vcf(vcf_path, allele.genepanel[0], allele.genepanel[1])
            log.info("Deposited {} as single alleles".format(vcf_path))
            self.session.commit()

    def deposit_cnv_alleles(self):
        for allele in CNV_ALLELES:
            vcf_path = os.path.join(SCRIPT_DIR, allele["path"])
            da = DepositAlleles(self.session)
            da.import_vcf(vcf_path, allele["genepanel"][0], allele["genepanel"][1])
            log.info("Deposited {} as single alleles".format(vcf_path))
            self.session.commit()

    def deposit_genepanels(self):
        dg = DepositGenepanel(self.session)
        for gpdata in GENEPANELS:
            dg.add_genepanel(
                os.path.join(SCRIPT_DIR, gpdata.transcripts),
                os.path.join(SCRIPT_DIR, gpdata.phenotypes),
                gpdata.name,
                gpdata.version,
                replace=False,
            )

    def deposit_references(self):
        references_path = os.path.join(SCRIPT_DIR, REFERENCES)
        import_references(self.session, references_path)

    def deposit_custom_annotation(self):
        custom_anno_path = os.path.join(SCRIPT_DIR, CUSTOM_ANNO)
        import_custom_annotations(self.session, custom_anno_path)

    def deposit_fixtures(self):
        log.info("Depositing test fixtures")
        alleleassessments = os.path.join(SCRIPT_DIR, FIXTURES, "alleleassessments.sql")
        os.system(f"cat {alleleassessments} | psql $DB_URL")

    def deposit_all(self, test_set: Optional[str] = None):

        if test_set not in AVAILABLE_TESTSETS:
            raise RuntimeError(
                "Test set {} not part of available test sets: {}".format(
                    test_set, ",".join(AVAILABLE_TESTSETS)
                )
            )

        log.info("--------------------")
        log.info("Starting a DB reset")
        log.info("on {}".format(os.getenv("DB_URL", "DB_URL NOT SET, BAD")))
        log.info("--------------------")
        self.deposit_annotation_config()
        self.deposit_genepanels()
        self.deposit_users()
        self.deposit_filter_configs()
        self.deposit_references()
        if test_set in [SPECIAL_TESTSET_SKIPPING_VCF.upper(), SPECIAL_TESTSET_SKIPPING_VCF.lower()]:
            log.info("Skipping deposit of vcf and custom annotations")
        else:
            self.deposit_analyses(test_set=test_set)
            self.deposit_alleles()
            self.deposit_cnv_alleles()
            self.deposit_custom_annotation()
            if test_set == "default":
                self.deposit_fixtures()

        log.info("--------------------")
        log.info(" DB Reset Complete!")
        log.info("--------------------")


if __name__ == "__main__":

    import argparse
    from applogger import setup_logger

    setup_logger()

    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--testset",
        action="store",
        dest="testset",
        help="Name of testset to import",
        default="default",
    )

    args = parser.parse_args()

    db = DB()
    db.connect()
    dt = DepositTestdata(db)
    dt.deposit_all(test_set=args.testset)
