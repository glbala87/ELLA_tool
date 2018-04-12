#!/usr/bin/env python
"""
Code for adding or modifying gene panels in varDB.
"""

import os
import sys
import logging
import json
import glob
import re

SPECIAL_TESTSET_SKIPPING_VCF = "empty"

logging.basicConfig(level=logging.DEBUG)

import vardb.datamodel
from vardb.datamodel import DB
from vardb.deposit.deposit_genepanel import DepositGenepanel
from vardb.deposit.deposit_references import import_references
from vardb.deposit.deposit_custom_annotations import import_custom_annotations
from vardb.deposit.deposit_users import import_users, import_groups
from vardb.deposit.deposit_analysis import DepositAnalysis
from vardb.deposit.deposit_alleles import DepositAlleles
from vardb.watcher.analysis_watcher import AnalysisConfigData

from vardb.util import vcfiterator

log = logging.getLogger(__name__)

SCRIPT_DIR = os.path.abspath(os.path.dirname(__file__))


# Paths are relative to script dir.
# See vardb/datamodel/genepanel-config-schema.json for format of genepanel config

USERS = '../testdata/users.json'
USERGROUPS = '../testdata/usergroups.json'

REPORT_EXAMPLE = '''
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
'''

WARNINGS_EXAMPLE = '''
2 regions have too low coverage
chr7:g.6013138N>N chr7:g.6013175N>N
chr2:g.48010497N>N chr2:g.48010531N>N
'''

GENEPANELS = [
    {
        'transcripts': '../testdata/clinicalGenePanels/OMIM_v01/OMIM_v01.transcripts.csv',
        'phenotypes': '../testdata/clinicalGenePanels/OMIM_v01/OMIM_v01.phenotypes.csv',
        'name': 'OMIM',
        'version': 'v01'
    },
    {
        'transcripts': '../testdata/clinicalGenePanels/HBOCUTV_v01/HBOCUTV_v01.transcripts.csv',
        'phenotypes': '../testdata/clinicalGenePanels/HBOCUTV_v01/HBOCUTV_v01.phenotypes.csv',
        'name': 'HBOCUTV',
        'version': 'v01'
    },
    {
        'config': '../testdata/clinicalGenePanels/HBOC_v01/HBOC_v01.config.json',
        'transcripts': '../testdata/clinicalGenePanels/HBOC_v01/HBOC_v01.transcripts.csv',
        'phenotypes': '../testdata/clinicalGenePanels/HBOC_v01/HBOC_v01.phenotypes.csv',
        'name': 'HBOC',
        'version': 'v01'
    },
    {
        'transcripts': '../testdata/clinicalGenePanels/Ciliopati_v05/Ciliopati_v05.transcripts.csv',
        'phenotypes': '../testdata/clinicalGenePanels/Ciliopati_v05/Ciliopati_v05.phenotypes.csv',
        'name': 'Ciliopati',
        'version': 'v05'
    }
]


ANALYSES = [
    {
        'path': '../testdata/analyses/small',
        'name': 'small',
        'default': True,
    },
    {
        'path': '../testdata/analyses/e2e',
        'name': 'e2e'
    },
    {
        'path': '../testdata/analyses/integration_testing',
        'name': 'integration_testing',
    },
    {
        'path': '../testdata/analyses/custom',
        'name': 'custom',
    },
    {
        'path': '../testdata/analyses/sanger',
        'name': 'sanger',
    },
]

ALLELES = [
    {
        'path': '../testdata/analyses/small/brca_sample_1.HBOC_v01/brca_sample_1.HBOC_v01.vcf',
        'genepanel': ('HBOC', 'v01')
    }
]

DEFAULT_TESTSET = filter(lambda a:  'default' in a and a['default'], ANALYSES)[0]['name']
AVAILABLE_TESTSETS = [SPECIAL_TESTSET_SKIPPING_VCF] + map(lambda a: a['name'], ANALYSES)

REFERENCES = '../testdata/references_test.json'
CUSTOM_ANNO = '../testdata/custom_annotation_test.json'


class DepositTestdata(object):

    ANALYSIS_FILE_RE = re.compile('(?P<analysis_name>.+\.(?P<genepanel_name>.+)_(?P<genepanel_version>.+))\.vcf')

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

    def deposit_analyses(self, test_set=None):
        """
        :param test_set: Which set to import.
        """

        if test_set is None:
            testset = next(v for v in ANALYSES if v.get('default'))
        else:
            testset = next(v for v in ANALYSES if v['name'] == test_set)

        testset_path = os.path.join(SCRIPT_DIR, testset['path'])
        analysis_paths = [os.path.join(testset_path, d) for d in os.listdir(testset_path)]
        analysis_paths.sort()
        for analysis_path in analysis_paths:

            if not os.path.isdir(analysis_path):
                continue
            try:
                analysis_vcf_path = glob.glob(os.path.join(analysis_path, '*.vcf'))[0]
                filename = os.path.basename(analysis_vcf_path)
                matches = re.match(DepositTestdata.ANALYSIS_FILE_RE, filename)

                analysis_name = matches.group('analysis_name')
                gp_name = matches.group('genepanel_name')
                gp_version = matches.group('genepanel_version')

                da = DepositAnalysis(self.session)
                acd = AnalysisConfigData(
                    analysis_vcf_path,
                    analysis_name,
                    gp_name,
                    gp_version,
                    "1",
                    warnings=WARNINGS_EXAMPLE if gp_name == 'HBOCUTV' else None,
                    report=REPORT_EXAMPLE
                )

                da.import_vcf(acd)

                log.info("Deposited {} as analysis".format(analysis_name))
                self.session.commit()

            except UserWarning as e:
                log.exception(str(e))
                sys.exit()

    def deposit_alleles(self):

        for allele in ALLELES:
            vcf_path = os.path.join(SCRIPT_DIR, allele['path'])

            da = DepositAlleles(self.session)
            da.import_vcf(
                vcf_path,
                allele['genepanel'][0],
                allele['genepanel'][1]
            )
            log.info("Deposited {} as single alleles".format(vcf_path))
            self.session.commit()

    def deposit_genepanels(self):
        dg = DepositGenepanel(self.session)
        for gpdata in GENEPANELS:
            dg.add_genepanel(
                os.path.join(SCRIPT_DIR,  gpdata['transcripts'] if 'transcripts' in gpdata else gpdata['path']),
                os.path.join(SCRIPT_DIR,  gpdata['phenotypes']) if 'phenotypes' in gpdata else None,
                gpdata['name'],
                gpdata['version'],
                configPath=os.path.join(SCRIPT_DIR,  gpdata['config']) if 'config' in gpdata else None,
                replace=True
            )

    def deposit_references(self):
        references_path = os.path.join(SCRIPT_DIR, REFERENCES)
        import_references(self.session, references_path)

    def deposit_custom_annotation(self):
        custom_anno_path = os.path.join(SCRIPT_DIR, CUSTOM_ANNO)
        import_custom_annotations(self.session, custom_anno_path)

    def deposit_all(self, test_set=None):

        if test_set not in AVAILABLE_TESTSETS:
            raise RuntimeError("Test set {} not part of available test sets: {}".format(test_set, ','.join(AVAILABLE_TESTSETS)))

        log.info("--------------------")
        log.info("Starting a DB reset")
        log.info("on {}".format(os.getenv('DB_URL', 'DB_URL NOT SET, BAD')))
        log.info("--------------------")
        self.deposit_genepanels()
        self.deposit_users()
        self.deposit_references()
        if test_set in [SPECIAL_TESTSET_SKIPPING_VCF.upper(), SPECIAL_TESTSET_SKIPPING_VCF.lower()]:
            log.info("Skipping deposit of vcf and custom annotations")
        else:
            self.deposit_analyses(test_set=test_set)
            self.deposit_alleles()
            self.deposit_custom_annotation()

        log.info("--------------------")
        log.info(" DB Reset Complete!")
        log.info("--------------------")


if __name__ == "__main__":

    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--testset", action="store", dest="testset", help="Name of testset to import", default="small")

    args = parser.parse_args()

    db = DB()
    db.connect()
    dt = DepositTestdata(db)
    dt.deposit_all(test_set=args.testset)
