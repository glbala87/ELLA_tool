#!/usr/bin/env python
"""
Code for adding or modifying gene panels in varDB.
"""

import os
import sys
import logging
import json

logging.basicConfig(level=logging.DEBUG)

import vardb.datamodel
from vardb.datamodel import DB
from vardb.deposit.deposit_genepanel import DepositGenepanel
from vardb.deposit.deposit_references import import_references
from vardb.deposit.deposit_users import import_users
from vardb.deposit.deposit import Importer

log = logging.getLogger(__name__)

SCRIPT_DIR = os.path.abspath(os.path.dirname(__file__))


# Paths are relative to script dir

USERS = '../testdata/users.json'

GENEPANELS = [
    {
        'transcripts': '../testdata/clinicalGenePanels/HBOC_OUS_medGen_v00_b37/HBOC_OUS_medGen_v00_b37.transcripts.csv',
        'phenotypes': '../testdata/clinicalGenePanels/HBOC_OUS_medGen_v00_b37/HBOC_OUS_medGen_v00_b37.phenotypes.csv',
        'name': 'HBOC',
        'version': 'v00'
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


VCF_SMALL = [
    # {
    #     'path': '../testdata/brca_s1_v1.vcf',
    #     'gp': 'HBOC',
    #     'gp_version': 'v00'
    # },
    # {
    #     'path': '../testdata/brca_s2_v1.vcf',
    #     'gp': 'HBOC',
    #     'gp_version': 'v00'
    # },
    # {
    #     'path': '../testdata/brca_HDepositFirst.vcf',
    #     'gp': 'HBOC',
    #     'gp_version': 'v00',
    #     'import_assessments': True
    # },
    # {
    #     'path': '../testdata/brca_H01.vcf',
    #     'gp': 'HBOC',
    #     'gp_version': 'v00'
    # },
    # {
    #     'path': '../testdata/brca_H02.vcf',
    #     'gp': 'HBOC',
    #     'gp_version': 'v00'
    # },
    {
        'path': '../testdata/brca_sample_1.vcf',
        'gp': 'HBOC',
        'gp_version': 'v00'
    },
    {
        'path': '../testdata/brca_sample_2.vcf',
        'gp': 'HBOC',
        'gp_version': 'v00'
    },
    {
        'path': '../testdata/brca_sample_3.vcf',
        'gp': 'HBOC',
        'gp_version': 'v00'
    },
    {
        'path': '../testdata/brca_sample_4.vcf',
        'gp': 'HBOC',
        'gp_version': 'v00'
    },
    {
        'path': '../testdata/brca_sample_5.vcf',
        'gp': 'HBOC',
        'gp_version': 'v00'
    },
    {
        'path': '../testdata/brca_sample_6.vcf',
        'gp': 'HBOC',
        'gp_version': 'v00'
    },
    {
        'path': '../testdata/brca_sample_7.vcf',
        'gp': 'HBOC',
        'gp_version': 'v00'
    },
    {
        'path': '../testdata/brca_sample_8.vcf',
        'gp': 'HBOC',
        'gp_version': 'v00'
    },
    {
        'path': '../testdata/brca_sample_master.vcf',
        'gp': 'HBOC',
        'gp_version': 'v00'
    },

]

VCF_LARGE = VCF_SMALL + [
    {
        'path': '../testdata/na12878.bindevev.transcripts.annotated.vcf',
        'gp': 'Bindevev',
        'gp_version': 'v02'
    },
    {
        'path': '../testdata/na12878.Ciliopati.transcripts.annotated.vcf',
        'gp': 'Ciliopati',
        'gp_version': 'v03'
    },
    {
        'path': '../testdata/na12878.EEogPU.transcripts.annotated.vcf',
        'gp': 'EEogPU',
        'gp_version': 'v02'
    },
    {
        'path': '../testdata/na12878.Iktyose.transcripts.annotated.vcf',
        'gp': 'Iktyose',
        'gp_version': 'v02'
    },
    {
        'path': '../testdata/na12878.Joubert.transcripts.annotated.vcf',
        'gp': 'Joubert',
        'gp_version': 'v02'
    }

]

VCF_TESTSET = [
    {
        'path': '../testdata/brca_sample_1.vcf',
        'gp': 'HBOC',
        'gp_version': 'v00'
    },
    {
        'path': '../testdata/brca_sample_2.vcf',
        'gp': 'HBOC',
        'gp_version': 'v00'
    },
    {
        'path': '../testdata/brca_sample_master.vcf',
        'gp': 'HBOC',
        'gp_version': 'v00'
    }
]


class DepositTestdata(object):

    def __init__(self, db):
        self.engine = db.engine
        self.session = db.session

    def remake_db(self):
        # We must import all models before recreating database
        from vardb.datamodel import allele, genotype, assessment, sample, patient, disease, gene, annotation  # needed

        vardb.datamodel.Base.metadata.drop_all(self.engine)
        vardb.datamodel.Base.metadata.create_all(self.engine)

    def deposit_users(self):
        with open(os.path.join(SCRIPT_DIR, USERS)) as f:
            import_users(self.session, json.load(f))

    def deposit_vcfs(self, test_set=None):
        """
        :param test_set: Which set to import. Valid values: 'small', 'large', 'test'. Default: 'small'
        """

        test_sets = {
            'small': VCF_SMALL,
            'large': VCF_LARGE,
            'test': VCF_TESTSET
        }

        vcfs = test_sets.get(test_set, VCF_SMALL)

        for vcfdata in vcfs:
            importer = Importer(self.session)
            try:
                kwargs = {
                    'genepanel_name': vcfdata['gp'],
                    'genepanel_version': vcfdata['gp_version'],
                    'import_assessments': vcfdata.get('import_assessments', False)
                }
                importer.importVcf(
                    os.path.join(SCRIPT_DIR, vcfdata['path']),
                    **kwargs
                )
                log.info("Deposited {}".format(vcfdata['path']))
                self.session.commit()

            except UserWarning as e:
                log.exception(str(e))
                sys.exit()

    def deposit_genepanels(self):
        dg = DepositGenepanel(self.session)
        for gpdata in GENEPANELS:
            dg.add_genepanel(
                os.path.join(SCRIPT_DIR,  gpdata['transcripts'] if 'transcripts' in gpdata else gpdata['path']),
                os.path.join(SCRIPT_DIR,  gpdata['phenotypes'] if 'phenotypes' in gpdata else None),
                gpdata['name'],
                gpdata['version'],
                force_yes=True
            )

    def deposit_references(self):
        import_references(self.engine)

    def deposit_all(self, test_set=None):
        log.info("--------------------")
        log.info("Starting a DB reset")
        log.info("on {}".format(os.getenv('DB_URL', 'DB_URL NOT SET, BAD')))
        log.info("--------------------")
        self.remake_db()
        self.deposit_users()
        self.deposit_genepanels()
        self.deposit_references()
        self.deposit_vcfs(test_set=test_set)
        log.info("--------------------")
        log.info(" DB Reset Complete!")
        log.info("--------------------")


if __name__ == "__main__":
    db = DB()
    db.connect()
    dt = DepositTestdata(db)
    dt.deposit_all()
