#!/usr/bin/env python
"""
Code for loading the contents of VCF files into the vardb database.

Use one transaction for whole file, and prompts user before committing.
Adds annotation if supplied annotation is different than what is already in db.
Can use specific annotation parsers to split e.g. allele specific annotation.
"""

import logging
from collections import OrderedDict

from vardb.util import vcfiterator
from vardb.deposit.importers import inDBInfoProcessor, SpliceInfoProcessor, HGMDInfoProcessor, SplitToDictInfoProcessor

from deposit_from_vcf import DepositFromVCF

log = logging.getLogger(__name__)


class DepositAnalysisAppend(DepositFromVCF):

    def process_records(self, records, db_analysis, vcf_sample_names, db_samples):
        for k, v in records.iteritems():
            # Import alleles
            db_alleles = []
            for record in v:
                new_db_alleles = self.allele_importer.process(record)

                # Import annotation
                self.annotation_importer.process(record, new_db_alleles)

                db_alleles += new_db_alleles

            # Compute and import genotypes
            for sample_name, db_sample in zip(vcf_sample_names, db_samples):
                self.genotype_importer.process(v, sample_name, db_analysis, db_sample, db_alleles)

    def import_vcf(self, path, analysis_name, gp_name, gp_version, cache_size=1000, sample_type="HTS"):

        vi = vcfiterator.VcfIterator(path)
        vi.addInfoProcessor(inDBInfoProcessor(vi.getMeta()))
        vi.addInfoProcessor(SpliceInfoProcessor(vi.getMeta()))
        vi.addInfoProcessor(HGMDInfoProcessor(vi.getMeta()))
        vi.addInfoProcessor(SplitToDictInfoProcessor(vi.getMeta()))

        vcf_sample_names = vi.samples

        db_genepanel = self.get_genepanel(gp_name, gp_version)
        db_analysis = self.analysis_importer.get(
            analysis_name,
            db_genepanel
        )
        db_samples = self.sample_importer.process(vcf_sample_names, db_analysis, sample_type)

        self.analysis_interpretation_importer.process(db_analysis, reopen_if_exists=True)
        records_cache = OrderedDict()
        N = 0
        for record in vi.iter():
            self.counter['nVariantsInFile'] += 1
            N += 1
            key = (record["CHROM"], record["POS"])
            if key not in records_cache:
                records_cache[key] = []

            assert len(record["ALT"]) == 1, "We only support decomposed variants. That is, only one ALT per line/record."

            if N < cache_size:
                records_cache[key].append(record)
                continue
            elif key in records_cache:
                # Make sure all variants at same position is in same cache
                records_cache[key].append(record)
                continue
            else:
                self.process_records(records_cache, db_analysis, vcf_sample_names, db_samples)

                records_cache.clear()
                records_cache[key].append(record)
                N = 1

        self.process_records(records_cache, db_analysis, vcf_sample_names, db_samples)
