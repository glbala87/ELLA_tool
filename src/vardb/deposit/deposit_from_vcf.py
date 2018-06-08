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

from api.config import config
import vardb.datamodel
from vardb.datamodel import gene
from vardb.util import vcfiterator
from vardb.deposit.importers import AnalysisImporter, AnnotationImporter, SampleImporter, \
                                    GenotypeImporter, AlleleImporter, AnalysisInterpretationImporter, \
                                    SpliceInfoProcessor, HGMDInfoProcessor, \
                                    SplitToDictInfoProcessor, AlleleInterpretationImporter


log = logging.getLogger(__name__)


class DepositFromVCF(object):

    def __init__(self, session):
        self.session = session
        self.sample_importer = SampleImporter(self.session)
        self.annotation_importer = AnnotationImporter(self.session)
        self.allele_importer = AlleleImporter(self.session)
        self.genotype_importer = GenotypeImporter(self.session)
        self.analysis_importer = AnalysisImporter(self.session)
        self.analysis_interpretation_importer = AnalysisInterpretationImporter(self.session)
        self.allele_interpretation_importer = AlleleInterpretationImporter(self.session)
        self.counter = defaultdict(int)

    def get_postprocessors(self, type):
        return [p for p in config['deposit']['postprocess'] if p['type'] == type]

    def get_genepanel(self, gp_name, gp_version):
        try:
            genepanel = self.session.query(gene.Genepanel).filter(and_(
                gene.Genepanel.name == gp_name,
                gene.Genepanel.version == gp_version)).one()
        except sqlalchemy.orm.exc.NoResultFound:
            log.warning("Genepanel {} version {} not available in varDB".format(
                gp_name, gp_version))
            raise RuntimeError("Genepanel {} version {} not available in varDB".format(
                gp_name, gp_version))
        return genepanel

    def import_vcf(self, path, sample_configs=None, analysis_config=None, assess_class=None):
        raise RuntimeError("import_vcf must be overloaded in subclass")

    def is_inside_transcripts(self, record, genepanel):
        chr = record["CHROM"]
        pos = record["POS"]-1 # We use zero-based transcripts
        for tx in genepanel.transcripts:
            if chr == tx.chromosome and (tx.tx_start <= pos <= tx.tx_end):
                return True
        return False

    def get_allele_from_record(self, record, alleles):
        for allele in alleles:
            if allele['chromosome'] == record['CHROM'] and \
                allele['vcf_pos'] == record['POS'] and \
                allele['vcf_ref'] == record['REF'] and \
                allele['vcf_alt'] == record['ALT'][0]:
                return allele
        return None

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
