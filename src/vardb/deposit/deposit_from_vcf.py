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

    def import_vcf(self, path, sample_configs=None, analysis_config=None, assess_class=None):
        raise RuntimeError("import_vcf must be overloaded in subclass")

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
