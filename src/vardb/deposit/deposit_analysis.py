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
from collections import OrderedDict

from vardb.util import DB, vcfiterator
from vardb.deposit.importers import SpliceInfoProcessor, HGMDInfoProcessor, SplitToDictInfoProcessor

from deposit_from_vcf import DepositFromVCF

log = logging.getLogger(__name__)


class DepositAnalysis(DepositFromVCF):

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

    def import_vcf(self, analysis_config_data, cache_size=1000, sample_type="HTS"):

        vi = vcfiterator.VcfIterator(analysis_config_data.vcf_path)
        vi.addInfoProcessor(SpliceInfoProcessor(vi.getMeta()))
        vi.addInfoProcessor(HGMDInfoProcessor(vi.getMeta()))
        vi.addInfoProcessor(SplitToDictInfoProcessor(vi.getMeta()))

        vcf_sample_names = vi.samples

        db_genepanel = self.get_genepanel(analysis_config_data.gp_name, analysis_config_data.gp_version)
        db_analysis = self.analysis_importer.process(analysis_config_data.analysis_name, db_genepanel)
        db_samples = self.sample_importer.process(vcf_sample_names, db_analysis, sample_type)

        if not db_samples or len(db_samples) != len(vcf_sample_names):
            self.session.rollback()
            raise RuntimeError("Couldn't import samples to database. (db_samples: %s, vcf_sample_names: %s)" %(str(db_samples), str(vcf_sample_names)))

        self.analysis_interpretation_importer.process(db_analysis)
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


def main(argv=None):
    """Example: ./deposit.py --vcf=./myvcf.vcf"""
    argv = argv or sys.argv[1:]
    parser = argparse.ArgumentParser(description="""Deposit variants and genotypes from a VCF file into varDB.""")
    parser.add_argument("--vcf", action="store", dest="vcfPath", required=True, help="Path to VCF file to deposit")
    parser.add_argument("--samplecfgs", action="store", nargs="+", dest="sample_config_files", required=True,
                        help="Configuration file(s) (JSON) for sample(s) from pipeline")
    parser.add_argument("--analysiscfg", action="store", dest="analysis_config_file", required=True,
                        help="Configuration file (JSON) for analysis from pipeline")
    parser.add_argument("--skip", action="store", dest="skipInfoFields", required=False, nargs='*',
                        default=["NS", "DP", "AN", "CIGAR"],
                        help="The VCF INFO fields that should NOT be added as annotation to varDB.")
    parser.add_argument("--refgenome", action="store", dest="refGenome", required=False,
                        default="GRCh37", help="Reference genome name")
    parser.add_argument("-f", action="store_true", dest="nonInteractive", required=False,
                        default=False, help="Do not ask for confirmation before deposit")

    args = parser.parse_args(argv)

    sample_configs = list()
    for sample_config_file in args.sample_config_files:
        with open(sample_config_file) as f:
            sample_configs.append(json.load(f))

    with open(args.analysis_config_file) as f:
        analysis_config = json.load(f)

    db = DB()
    db.connect()
    session = db.session

    da = DepositAnalysis(session)
    try:
        da.import_vcf(
            args.vcfPath,
            sample_configs=sample_configs,
            analysis_config=analysis_config
        )
    except UserWarning as e:
        log.error(str(e))
        sys.exit()

    if not args.nonInteractive:
        print "You are about to commit the following changes to the database:"
        da.printStats()
        print "Proceed? (Y/n)"
        if not raw_input() == "Y":
            log.warning("Aborting deposit! Rolling back changes.")
            session.rollback()
            return -1

    session.commit()
    print "Deposit complete."
    return 0

if __name__ == "__main__":
    sys.exit(main())
