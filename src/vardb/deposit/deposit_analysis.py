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
from vardb.deposit.importers import AnalysisImporter, AnnotationImporter, SampleImporter, \
                                    GenotypeImporter, AlleleImporter, AnalysisInterpretationImporter, \
                                    SpliceInfoProcessor, HGMDInfoProcessor, \
                                    SplitToDictInfoProcessor, AlleleInterpretationImporter, \
                                    batch_generator

from vardb.datamodel import sample, workflow

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

    def import_vcf(self, analysis_config_data, batch_size=1000, sample_type="HTS", ped_file=None, append=False):

        vi = vcfiterator.VcfIterator(analysis_config_data.vcf_path)
        vi.addInfoProcessor(SpliceInfoProcessor(vi.getMeta()))
        vi.addInfoProcessor(HGMDInfoProcessor(vi.getMeta()))
        vi.addInfoProcessor(SplitToDictInfoProcessor(vi.getMeta()))

        vcf_sample_names = vi.samples

        db_genepanel = self.get_genepanel(analysis_config_data.gp_name, analysis_config_data.gp_version)

        if not append:
            db_analysis = self.analysis_importer.process(
                analysis_config_data.analysis_name,
                analysis_config_data.priority,
                db_genepanel,
                analysis_config_data.report,
                analysis_config_data.warnings
            )
        else:
            db_analysis = self.session.query(sample.Analysis).filter(
                sample.Analysis.name == analysis_config_data.analysis_name
            ).one()

            if any(s for s in db_analysis.samples if s.father_id is not None or s.mother_id is not None):
                raise RuntimeError("Appending to a family analysis is not supported.")

        db_analysis_interpretation = self.analysis_interpretation_importer.process(db_analysis, reopen_if_exists=append)
        db_samples = self.sample_importer.process(vcf_sample_names, db_analysis, sample_type=sample_type, ped_file=ped_file)

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

        proband_sample_name = next(s.identifier for s in db_samples if s.proband is True)

        needs_secondallele = {s: False for s in vcf_sample_names}
        sample_has_coverage = {s: False for s in vcf_sample_names}
        proband_records = []  # One or two records belonging to proband
        proband_alleles = []  # One or two alleles belonging to proband, for creating one genotype
        for batch_records in batch_generator(vi.iter, batch_size):

            # Multiallelic blocks:
            # Due to the nature of decomposed + normalized variants, we need to be careful how we
            # process the data. Variants belonging to the same sample's genotype can be on different positions
            # after decomposition. Example:
            # Normal:
            # 10    ATT A,AG,ATC    0/1 1/2 2/3
            # After decompose/normalize:
            # 10    ATT A   0/1 1/. ./.
            # 11    TT   G   ./. ./1 1/.
            # 12    T   C   ./. ./. ./1
            #
            # For a genotype, we want to keep connection to both alleles (using genotype.secondallele_id).
            # For the proband sample, if the variant genotype is:
            # - '0/0', '0/.' or './.': we don't have any variant, ignore it.
            # - '0/1' or '1/1' we can import Genotype directly using a single allele.
            # - '1/.' we need to wait for next './1' entry in order to connect the second allele.
            #
            # Since we receive records one by one, we need to make sure we have all the necessary records
            # belonging to one multiallelic "block" from the vcf file. This is tracked by the needs_secondallele
            # attribute, tracking whether a sample is waiting for another multiallelic match.

            # First import whole batch as alleles
            for record in batch_records:

                if not self.is_inside_transcripts(record, db_genepanel):
                    error = "The following variant is not inside the genepanel %s\n" % (db_genepanel.name + "_" + db_genepanel.version)
                    error += "%s\t%s\t%s\t%s\t%s\n" % (record["CHROM"], record["POS"], record["ID"], record["REF"], ",".join(record["ALT"]))
                    raise RuntimeError(error)

                # If no data for proband, just skip the record
                if record['SAMPLES'][proband_sample_name]['GT'] in ['0/0', './.', '0/.', './0']:
                    continue

                self.allele_importer.add(record)

            alleles = self.allele_importer.process()

            for idx, record in enumerate(batch_records):
                for sample_name in vcf_sample_names:
                    # Track samples that have no coverage within a multiallelic block
                    # './.' often occurs for single records when the sample has genotype in other records,
                    # but if it is './.' in _all_ records within a block, it has no coverage at this site
                    if record['SAMPLES'][sample_name]['GT'] != './.':
                        sample_has_coverage[sample_name] = True

                    if record['SAMPLES'][sample_name]['GT'] in ['1/.', './1']:
                        needs_secondallele[sample_name] = not needs_secondallele[sample_name]

                # If no data for proband, don't add the record
                if record['SAMPLES'][proband_sample_name]['GT'] not in ['0/0', './.', '0/.', './0']:
                    allele = self.get_allele_from_record(record, alleles)

                    # Annotation
                    self.annotation_importer.add(record, allele['id'])
                    proband_alleles.append(allele)
                    proband_records.append(record)

                # Genotype
                # Run this always, since a "block" can be finished on records with no proband data
                if not any(needs_secondallele.values()) and proband_records:
                    assert len(proband_alleles) == len(proband_records)
                    samples_missing_coverage = [k for k, v in sample_has_coverage.iteritems() if not v]
                    self.genotype_importer.add(proband_records, proband_alleles, proband_sample_name, db_samples, samples_missing_coverage)
                    sample_has_coverage = {s: False for s in vcf_sample_names}
                    proband_records = []
                    proband_alleles = []

            annotations = self.annotation_importer.process()
            assert len(alleles) == len(annotations)

            genotypes, genotypesamplesdata = self.genotype_importer.process()

        assert len(proband_alleles) == 0
        assert len(proband_records) == 0

        if not append:
            self.postprocess(db_analysis, db_analysis_interpretation)

        self.session.commit()



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
