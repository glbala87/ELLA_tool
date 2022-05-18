#!/usr/bin/env python
"""
Code for loading the contents of VCF files into the vardb database.

Use one transaction for whole file, and prompts user before committing.
Adds annotation if supplied annotation is different than what is already in db.
Can use specific annotation parsers to split e.g. allele specific annotation.
"""

import logging
from typing import List, Optional

from vardb.deposit.importers import batch_generator
from vardb.util import vcfiterator
from vardb.util.vcfrecord import VCFRecord

from .deposit_from_vcf import DepositFromVCF

log = logging.getLogger(__name__)

BATCH_SIZE = 1000


class DepositAlleles(DepositFromVCF):
    def import_vcf(
        self,
        path: str,
        gp_name: Optional[str] = None,
        gp_version: Optional[str] = None,
        annotation_only: bool = False,
    ):
        vi = vcfiterator.VcfIterator(path)

        db_genepanel = None
        if gp_name and gp_version:
            db_genepanel = self.get_genepanel(gp_name, gp_version)

        batch_records: List[VCFRecord]
        for batch_records in batch_generator(iter(vi), BATCH_SIZE):
            if not annotation_only:
                assert db_genepanel, "Must specify genepanel if importing more than annotation"
                is_not_inside_transcripts: List[VCFRecord] = []
                for record in batch_records:
                    # When importing vcf we keep structural variants outside of transcripts,
                    # they can still be filtered using the filterchains
                    if not self.is_inside_transcripts(
                        record, db_genepanel
                    ) and not record.variant.INFO.get("SVTYPE"):
                        is_not_inside_transcripts.append(record)

                if is_not_inside_transcripts:
                    error = f"The following variants are not inside the genepanel {db_genepanel.name}_{db_genepanel.version}\n"
                    for record in is_not_inside_transcripts:
                        record_str = "\t".join(
                            [
                                str(record.variant.CHROM),
                                str(record.variant.POS),
                                str(record.variant.ID),
                                str(record.variant.REF),
                                ",".join([str(x) for x in record.variant.ALT]),
                            ]
                        )
                        error += record_str + "\n"
                    raise RuntimeError(error)

            for record in batch_records:
                self.allele_importer.add(record)

            alleles = self.allele_importer.process()

            for record in batch_records:
                rec_allele = record.get_allele(alleles)
                if not rec_allele:
                    raise RuntimeError(f"Could not find allele for {record!r}")
                self.annotation_importer.add(record, rec_allele["id"])

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
