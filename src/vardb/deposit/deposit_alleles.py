#!/usr/bin/env python
"""
Code for loading the contents of VCF files into the vardb database.

Use one transaction for whole file, and prompts user before committing.
Adds annotation if supplied annotation is different than what is already in db.
Can use specific annotation parsers to split e.g. allele specific annotation.
"""

import logging

from vardb.util import vcfiterator
from vardb.deposit.importers import batch_generator, HGMDInfoProcessor, SplitToDictInfoProcessor

from deposit_from_vcf import DepositFromVCF

log = logging.getLogger(__name__)

BATCH_SIZE = 1000


class DepositAlleles(DepositFromVCF):
    def import_vcf(self, path, gp_name=None, gp_version=None, annotation_only=False):
        vi = vcfiterator.VcfIterator(path)
        vi.addInfoProcessor(HGMDInfoProcessor(vi.getMeta()))
        vi.addInfoProcessor(SplitToDictInfoProcessor(vi.getMeta()))

        if not annotation_only:
            db_genepanel = self.get_genepanel(gp_name, gp_version)
            is_not_inside_transcripts = []
            for record in vi.iter():
                if not self.is_inside_transcripts(record, db_genepanel):
                    is_not_inside_transcripts.append(record)

            if is_not_inside_transcripts:
                error = "The following variants are not inside the genepanel %s\n" % (
                    db_genepanel.name + "_" + db_genepanel.version
                )
                for record in is_not_inside_transcripts:
                    error += "%s\t%s\t%s\t%s\t%s\n" % (
                        record["CHROM"],
                        record["POS"],
                        record["ID"],
                        record["REF"],
                        ",".join(record["ALT"]),
                    )
                raise RuntimeError(error)

        for batch_records in batch_generator(vi.iter, BATCH_SIZE):

            for record in batch_records:
                self.allele_importer.add(record)

            alleles = self.allele_importer.process()

            for record in batch_records:
                allele = self.get_allele_from_record(record, alleles)
                self.annotation_importer.add(record, allele["id"])

            # Import annotation for these alleles
            annotations = self.annotation_importer.process()

            assert len(alleles) == len(annotations)

            if not annotation_only:
                # Create allele interpretations so variant shows up in variant workflow view
                for allele in alleles:
                    self.allele_interpretation_importer.process(db_genepanel, allele["id"])

            self.counter["nVariantsInFile"] += 1
            if self.counter["nVariantsInFile"] % 10000 == 0:
                log.info("{} variants processed".format(self.counter["nVariantsInFile"]))
