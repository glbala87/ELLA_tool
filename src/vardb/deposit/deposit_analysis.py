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


log = logging.getLogger(__name__)


class DepositAnalysis(object):

    def __init__(self, session):
        self.session = session
        self.sample_importer = SampleImporter(self.session)
        self.annotation_importer = AnnotationImporter(self.session)
        self.allele_importer = AlleleImporter(self.session)
        self.genotype_importer = GenotypeImporter(self.session)
        self.analysis_importer = AnalysisImporter(self.session)
        self.analysis_interpretation_importer = AnalysisInterpretationImporter(self.session)
        self.counter = defaultdict(int)

    def check_samples(self, sample_names_in_vcf, sample_configs):
        """
        Returns name of sample(s) where:
        - Name of sample in VCF matches name in sample_config (if given).
        """
        for sample_name in sample_names_in_vcf:
            if sample_name not in [s['name'] for s in sample_configs]:
                raise RuntimeError("Missing sample configuration for sample '{}' given in vcf".format(sample_name))
        return True

    def get_genepanel(self, analysis_config):
        genepanel_name = analysis_config["params"]["genepanel"].split('_')[0]
        genepanel_version = analysis_config["params"]["genepanel"].split('_')[1]
        try:
            genepanel = self.session.query(gene.Genepanel).filter(and_(
                gene.Genepanel.name == genepanel_name,
                gene.Genepanel.version == genepanel_version)).one()
        except sqlalchemy.orm.exc.NoResultFound:
            log.warning("Genepanel {} version {} not available in varDB".format(
                genepanel_name, genepanel_version))
            raise RuntimeError("Genepanel {} version {} not available in varDB".format(
                genepanel_name, genepanel_version))
        return genepanel

    def import_vcf(self, path, sample_configs=None, analysis_config=None,
                   skip_anno=None, assess_class=None):

        vi = vcfiterator.VcfIterator(path)
        vi.addInfoProcessor(inDBInfoProcessor(vi.getMeta()))
        vi.addInfoProcessor(SpliceInfoProcessor(vi.getMeta()))
        vi.addInfoProcessor(HGMDInfoProcessor(vi.getMeta()))
        vi.addInfoProcessor(SplitToDictInfoProcessor(vi.getMeta()))

        vcf_sample_names = vi.samples
        self.check_samples(vcf_sample_names, sample_configs)

        # Only import sample/analysis if not importing assessments
        db_samples = self.sample_importer.process(vcf_sample_names, sample_configs=sample_configs)

        if not db_samples or len(db_samples) != len(vcf_sample_names):
            raise RuntimeError("Couldn't import samples to database.")

        db_genepanel = self.get_genepanel(analysis_config)

        db_analysis = self.analysis_importer.process(
            db_samples,
            analysis_config=analysis_config,
            genepanel=db_genepanel
        )

        self.analysis_interpretation_importer.process(db_analysis)

        for record in vi.iter():
            # Import alleles for this record (regardless if it's in our specified sample set or not)
            db_alleles = self.allele_importer.process(record)

            # Import annotation for these alleles
            self.annotation_importer.process(record, db_alleles, skip_anno=skip_anno)

            for sample_name, db_sample in zip(vcf_sample_names, db_samples):
                self.genotype_importer.process(record, sample_name, db_analysis, db_sample, db_alleles)

            self.counter['nVariantsInFile'] += 1

    def getCounter(self):
        counter = dict(self.counter)
        counter.update(self.sample_importer.counter)
        counter.update(self.allele_importer.counter)
        counter.update(self.annotation_importer.counter)
        counter.update(self.genotype_importer.counter)
        return counter

    def printStats(self):
        stats = self.getCounter()
        print "Samples to add: {}".format(stats["nSamplesAdded"])
        print "Variants in file: {}".format(stats.get('nVariantsInFile', '???'))
        print "Alternative alleles to add: {}".format(stats.get('nAltAlleles', '???'))
        print "Novel alt alleles to add: {}".format(stats.get("nNovelAltAlleles", '???'))
        print
        print "Novel annotations to add: {}".format(stats.get("nNovelAnnotation", '???'))
        print "Updated annotations: {}".format(stats.get("nUpdatedAnnotation", '???'))
        print "Annotations unchanged: {}".format(stats.get("nNoChangeAnnotation", '???'))
        print
        print "Genotypes hetro ref: {}".format(stats.get('nGenotypeHetroRef', '???'))
        print "Genotypes homo nonref: {}".format(stats.get('nGenotypeHomoNonRef', '???'))
        print "Genotypes hetro nonref: {}".format(stats.get('nGenotypeHetroNonRef', '???'))
        print "Genotypes not added (not variant/not called/sample not added): {}".format(stats.get('nGenotypeNotAdded', '???'))


def main(argv=None):
    """Example: ./deposit.py --vcf=./myvcf.vcf"""
    argv = argv or sys.argv[1:]
    parser = argparse.ArgumentParser(description="""Deposit variants and genotypes from a VCF file into varDB.""")
    parser.add_argument("--vcf", action="store", dest="vcfPath", required=True, help="Path to VCF file to deposit")
    parser.add_argument("--samplecfgs", action="store", nargs="+", dest="sample_config_file", required=True,
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

    session = vardb.datamodel.Session()

    da = DepositAnalysis(session)
    try:
        da.import_vcf(
            args.vcfPath,
            sample_configs=sample_configs,
            analysis_config=analysis_config,
            skip_anno=args.skipInfoFields
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
