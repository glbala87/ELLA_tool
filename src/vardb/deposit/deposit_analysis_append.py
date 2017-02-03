#!/usr/bin/env python
"""
Code for loading the contents of VCF files into the vardb database.

Use one transaction for whole file, and prompts user before committing.
Adds annotation if supplied annotation is different than what is already in db.
Can use specific annotation parsers to split e.g. allele specific annotation.
"""

import sys
import argparse
import json
import logging
from collections import defaultdict

from sqlalchemy import and_
import sqlalchemy.orm.exc

import vardb.datamodel
from vardb.datamodel import gene
from vardb.util import vcfiterator
from vardb.deposit.importers import AnalysisImporter, AnnotationImporter, SampleImporter, \
                                    GenotypeImporter, AlleleImporter, AnalysisInterpretationImporter, \
                                    inDBInfoProcessor, SpliceInfoProcessor, HGMDInfoProcessor, \
                                    SplitToDictInfoProcessor

from deposit_from_vcf import DepositFromVCF

log = logging.getLogger(__name__)


class DepositAnalysisAppend(DepositFromVCF):

    def import_vcf(self, path, sample_configs=None, analysis_config=None, assess_class=None):

        vi = vcfiterator.VcfIterator(path)
        vi.addInfoProcessor(inDBInfoProcessor(vi.getMeta()))
        vi.addInfoProcessor(SpliceInfoProcessor(vi.getMeta()))
        vi.addInfoProcessor(HGMDInfoProcessor(vi.getMeta()))
        vi.addInfoProcessor(SplitToDictInfoProcessor(vi.getMeta()))

        vcf_sample_names = vi.samples
        self.check_samples(vcf_sample_names, sample_configs)

        # if not db_samples or len(db_samples) != len(vcf_sample_names):
        #     raise RuntimeError("Couldn't import samples to database.")

        db_genepanel = self.get_genepanel(analysis_config)

        db_analysis = self.analysis_importer.get(
            analysis_config=analysis_config,
            genepanel=db_genepanel
        )

        # Only import sample/analysis if not importing assessments
        db_samples = self.sample_importer.get(vcf_sample_names, db_analysis)

        self.analysis_interpretation_importer.process(db_analysis)

        for record in vi.iter():
            # Import alleles for this record (regardless if it's in our specified sample set or not)
            db_alleles = self.allele_importer.process(record)

            # Import annotation for these alleles
            self.annotation_importer.process(record, db_alleles)

            for sample_name, db_sample in zip(vcf_sample_names, db_samples):
                self.genotype_importer.process(record, sample_name, db_analysis, db_sample, db_alleles)

            self.counter['nVariantsInFile'] += 1
