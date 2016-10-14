#!/usr/bin/env python
"""
Code for adding or modifying gene panels in varDB.
"""

import os
import sys
import logging
import json
import glob

logging.basicConfig(level=logging.DEBUG)

import vardb.datamodel
from vardb.datamodel import DB
from vardb.deposit.deposit_genepanel import DepositGenepanel
from vardb.deposit.deposit_references import import_references
from vardb.deposit.deposit_users import import_users
from vardb.deposit.deposit_analysis import DepositAnalysis

from vardb.util import vcfiterator

log = logging.getLogger(__name__)

SCRIPT_DIR = os.path.abspath(os.path.dirname(__file__))


# Paths are relative to script dir.
# See vardb/datamodel/genap-genepanel-config-schema.json for format of genepanel config

USERS = '../testdata/users.json'

GENEPANELS = [
    {
        'transcripts': '../testdata/clinicalGenePanels/HBOCUTV_v01/HBOCUTV_v01.transcripts.csv',
        'phenotypes': '../testdata/clinicalGenePanels/HBOCUTV_v01/HBOCUTV_v01.phenotypes.csv',
        'name': 'HBOCUTV',
        'version': 'v01'
    },
    {'config': '../testdata/clinicalGenePanels/HBOC_v01/HBOC_v01.config.json',
     'transcripts': '../testdata/clinicalGenePanels/HBOC_v01/HBOC_v01.transcripts.csv',
     'phenotypes': '../testdata/clinicalGenePanels/HBOC_v01/HBOC_v01.phenotypes.csv',
     'name': 'HBOC',
     'version': 'v01'
     },
    {
        'path': '../testdata/clinicalGenePanels/Bindevev_v02.transcripts.csv',
        'name': 'Bindevev',
        'version': 'v02'
    },
    {
        'path': '../testdata/clinicalGenePanels/Ciliopati_v03.transcripts.csv',
        'name': 'Ciliopati',
        'version': 'v03'
    },
    {
        'path': '../testdata/clinicalGenePanels/EEogPU_v02.transcripts.csv',
        'name': 'EEogPU',
        'version': 'v02'
    },
    {
        'path': '../testdata/clinicalGenePanels/Iktyose_v02.transcripts.csv',
        'name': 'Iktyose',
        'version': 'v02'
    },
    {
        'path': '../testdata/clinicalGenePanels/Joubert_v02.transcripts.csv',
        'name': 'Joubert',
        'version': 'v02'
    }
]


VCF = [

    {
        'path': '../testdata/vcf/all',
        'name': 'all',
    },
    {
        'path': '../testdata/vcf/small',
        'name': 'small',
        'default': True,
    },
    {
        'path': '../testdata/vcf/e2e',
        'name': 'e2e'
    },
    {
        'path': '../testdata/vcf/integration_testing',
        'name': 'integration_testing',
    },
    {
        'path': '../testdata/vcf/custom',
        'name': 'custom',
    },
]

REFERENCES = '../testdata/references_test.json'

class DepositTestdata(object):

    def __init__(self, db):
        self.engine = db.engine
        self.session = db.session

    def _get_vcf_samples(self, vcf_path):
        vi = vcfiterator.VcfIterator(vcf_path)
        return vi.getSamples()

    def deposit_users(self):
        with open(os.path.join(SCRIPT_DIR, USERS)) as f:
            import_users(self.session, json.load(f))

    def deposit_vcfs(self, test_set=None):
        """
        :param test_set: Which set to import.
        """

        if test_set is None:
            testset = next(v for v in VCF if v.get('default'))
        else:
            testset = next(v for v in VCF if v['name'] == test_set)

        vcf_paths = glob.glob(os.path.join(SCRIPT_DIR, testset['path'], '*.vcf'))
        vcf_paths.sort()
        for vcf_path in vcf_paths:
            da = DepositAnalysis(self.session)
            try:
                vcf_path = os.path.join(SCRIPT_DIR, vcf_path)
                filename = os.path.basename(vcf_path)
                # Get last part of filename before ext 'sample.HBOC_v00.vcf'
                gp_part = os.path.splitext(filename)[0].split('.')[-1].split('_')

                kwargs = {
                    'sample_configs': [{
                        'name': self._get_vcf_samples(vcf_path)[0]
                    }],
                    'analysis_config': {
                        'name': '{}-{}-{}'.format(
                            self._get_vcf_samples(vcf_path)[0],
                            *gp_part
                        ),
                        'params': {
                            'genepanel': '_'.join(gp_part)
                        }
                    }
                }
                da.import_vcf(
                    vcf_path,
                    **kwargs
                )
                log.info("Deposited {} using panel {} {}".
                         format(vcf_path, gp_part[0], gp_part[1]))
                self.session.commit()

            except UserWarning as e:
                log.exception(str(e))
                sys.exit()

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

    def deposit_all(self, test_set=None):
        log.info("--------------------")
        log.info("Starting a DB reset")
        log.info("on {}".format(os.getenv('DB_URL', 'DB_URL NOT SET, BAD')))
        log.info("--------------------")
        self.deposit_users()
        self.deposit_genepanels()
        self.deposit_references()
        self.deposit_vcfs(test_set=test_set)
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
