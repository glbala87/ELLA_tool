#!/usr/bin/env python
"""
Code for loading the contents of VCF files into the vardb database.

Use one transaction for whole file, and prompts user before committing.
Adds annotation if supplied annotation is different than what is already in db.
Can use specific annotation parsers to split e.g. allele specific annotation.
"""

import sys
import re
import argparse
import json
import logging
import itertools
from collections import OrderedDict

from vardb.util import DB, vcfiterator
from vardb.deposit.importers import SpliceInfoProcessor, HGMDInfoProcessor, SplitToDictInfoProcessor
from vardb.datamodel import sample, allele, workflow

from deposit_from_vcf import DepositFromVCF

log = logging.getLogger(__name__)


class DepositAnalysis(DepositFromVCF):

    def postprocess(self, db_analysis, db_analysis_interpretation):
        candidate_processors = self.get_postprocessors('analysis')
        for c in candidate_processors:
            if re.search(c['name'], db_analysis.name):
                for method in c['methods']:
                    if method == 'analysis_not_ready_findings':
                        from .postprocessors import analysis_not_ready_findings  # FIXME: Has circular import, so must import here...
                        analysis_not_ready_findings(self.session, db_analysis, db_analysis_interpretation)

    def import_vcf(self, analysis_config_data, cache_size=1, sample_type="HTS", ped_file=None):

        vi = vcfiterator.VcfIterator(analysis_config_data.vcf_path)
        vi.addInfoProcessor(SpliceInfoProcessor(vi.getMeta()))
        vi.addInfoProcessor(HGMDInfoProcessor(vi.getMeta()))
        vi.addInfoProcessor(SplitToDictInfoProcessor(vi.getMeta()))

        vcf_sample_names = vi.samples

        db_genepanel = self.get_genepanel(analysis_config_data.gp_name, analysis_config_data.gp_version)
        db_analysis = self.analysis_importer.process(
            analysis_config_data.analysis_name,
            analysis_config_data.priority,
            db_genepanel,
            analysis_config_data.report,
            analysis_config_data.warnings
        )
        db_samples = self.sample_importer.process(vcf_sample_names, db_analysis, sample_type=sample_type, ped_file=ped_file)
        db_analysis_interpretation = self.analysis_interpretation_importer.process(db_analysis)

        # Due to the nature of decomposed + normalized variants, we need to be careful how we
        # process the data. Variants belonging to the same sample's genotype can be on different positions
        # after decomposition. Example:
        # Normal:
        # 10    ATT A,AG,ATC    0/1 1/2 2/3
        # After decompose/normalize:
        # 10    ATT A   0/1 1/. ./.
        # 11    TT   G   ./. ./1 1/.
        # 12    T   C   ./. ./. ./1

        # For a Genotype, we want to keep connection to both Alleles (using Genotype.secondallele_id).
        # For each sample, if the variant genotype is:
        # - '0/0' we don't have any variant, ignore it.
        # - '0/1' or '1/1' we can import Genotype directly using a single Allele.
        # - '1/.' we need to wait for next './1' entry in order to connect the second Allele.

        sample_needs_secondallele = {s: False for s in vcf_sample_names}
        sample_records = {s: [] for s in vcf_sample_names}
        sample_alleles = {s: [] for s in vcf_sample_names}
        for record in vi.iter():

            assert len(record["ALT"]) == 1, "Only decomposed variants are supported. That is, only one ALT per line/record."

            db_alleles = self.allele_importer.process(record)
            self.annotation_importer.process(record, db_alleles)

            assert len(db_alleles) == 1
            db_allele = db_alleles[0]

            for sample_name, sample_data in record['SAMPLES'].iteritems():
                assert '|' not in sample_data['GT'], 'Support for phased data is not implemented'
                assert sample_data['GT'] in ['./.', '0/0', '0/1', './1', '1/.', '1/1', '0/.'], 'Unrecognized genotype {}'.format(sample_data['GT'])

                if sample_data['GT'] in ['./.', '0/0', '0/.']:
                    continue

                sample_records[sample_name].append(record)
                sample_alleles[sample_name].append(db_allele)

                if sample_data['GT'] in ['./1', '1/.']:
                    sample_needs_secondallele[sample_name] = not sample_needs_secondallele[sample_name]

                # When we have all the alleles needed for the genotype (for this sample), create it
                if not sample_needs_secondallele[sample_name]:
                    db_sample = next(s for s in itertools.chain.from_iterable(db_samples.values()) if s.identifier == sample_name)
                    self.genotype_importer.process(sample_records[sample_name], sample_name, db_analysis, db_sample, sample_alleles[sample_name])
                    sample_records[sample_name] = []
                    sample_alleles[sample_name] = []
        self.postprocess(db_analysis, db_analysis_interpretation)


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
