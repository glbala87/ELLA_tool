#!/usr/bin/env python
"""
Code for loading the assessments of VCF files into the vardb database.

Use one transaction for whole file, and prompts user before committing.
"""

import sys
import argparse
import logging
from collections import defaultdict
from sqlalchemy import and_
import sqlalchemy.orm.exc

from vardb.datamodel import gene, DB
from vardb.util import vcfiterator
from vardb.deposit.importers import AnnotationImporter, AssessmentImporter, AlleleImporter, \
                                    SpliceInfoProcessor, HGMDInfoProcessor, \
                                    SplitToDictInfoProcessor

logging.basicConfig(level=logging.DEBUG)
log = logging.getLogger(__name__)


class DepositAssessments(object):

    def __init__(self, session):
        self.session = session
        self.annotation_importer = AnnotationImporter(self.session)
        self.assessment_importer = AssessmentImporter(self.session)
        self.allele_importer = AlleleImporter(self.session)
        self.counter = defaultdict(int)

    def get_genepanel(self, genepanel_name, genepanel_version):
        if genepanel_name is None or genepanel_version is None:
            log.warning("No genepanel/version supplied.")
            genepanel = None
        else:
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

    def import_vcf(self,
                   path,
                   genepanel_name=None,
                   genepanel_version=None):

        vi = vcfiterator.VcfIterator(path)
        vi.addInfoProcessor(SpliceInfoProcessor(vi.getMeta()))
        vi.addInfoProcessor(HGMDInfoProcessor(vi.getMeta()))
        vi.addInfoProcessor(SplitToDictInfoProcessor(vi.getMeta()))

        db_genepanel = self.get_genepanel(genepanel_name, genepanel_version)

        for record in vi.iter():
            # Import alleles for this record (regardless if it's in our specified sample set or not)
            db_alleles = self.allele_importer.process(record)

            # Import annotation for these alleles
            self.annotation_importer.process(record, db_alleles)

            # Import assessment for these alleles
            self.assessment_importer.process(
                record,
                db_alleles,
                genepanel=db_genepanel
            )
            self.counter['nVariantsInFile'] += 1

    def getCounter(self):
        counter = dict(self.counter)
        counter.update(self.allele_importer.counter)
        counter.update(self.annotation_importer.counter)
        counter.update(self.assessment_importer.counter)
        return counter

    def printStats(self):
        stats = self.getCounter()
        print "Variants in file: {}".format(stats.get('nVariantsInFile', '???'))
        print "Alternative alleles to add: {}".format(stats.get('nAltAlleles', '???'))
        print "Novel alt alleles to add: {}".format(stats.get("nNovelAltAlleles", '???'))
        print
        print "Novel annotations to add: {}".format(stats.get("nNovelAnnotation", '???'))
        print "Updated annotations: {}".format(stats.get("nUpdatedAnnotation", '???'))
        print "Annotations unchanged: {}".format(stats.get("nNoChangeAnnotation", '???'))
        print
        print "Novel assessments to add: {}".format(stats.get('nNovelAssessments', '???'))
        print "Updated assessments to add: {}".format(stats.get('nAssessmentsUpdated', '???'))
        print


def main(argv=None):
    """Example: ./deposit.py --vcf=./myvcf.vcf"""
    argv = argv or sys.argv[1:]
    parser = argparse.ArgumentParser(description="""Deposit variants and genotypes from a VCF file into varDB.""")
    parser.add_argument("--vcf", action="store", dest="vcfPath", required=True, help="Path to VCF file to deposit")
    parser.add_argument("--genepanel-name", action="store", dest="gp_name", required=True, help="Name of genepanel for assessments")
    parser.add_argument("--genepanel-version", action="store", dest="gp_version", required=True, help="Version of genepanel for assessments")

    parser.add_argument("-f", action="store_true", dest="nonInteractive", required=False,
                        default=False, help="Do not ask for confirmation before deposit")

    args = parser.parse_args(argv)

    db = DB()
    db.connect()
    da = DepositAssessments(db.session)
    try:
        da.import_vcf(
            args.vcfPath,
            genepanel_name=args.gp_name,
            genepanel_version=args.gp_version,
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
            db.session.rollback()
            return -1

    db.session.commit()
    print "Deposit complete."
    return 0

if __name__ == "__main__":
    sys.exit(main())
