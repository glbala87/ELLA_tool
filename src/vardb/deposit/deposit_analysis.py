#!/usr/bin/env python
"""
Code for loading the contents of VCF files into the vardb database.

Use one transaction for whole file, and prompts user before committing.
Adds annotation if supplied annotation is different than what is already in db.
Can use specific annotation parsers to split e.g. allele specific annotation.
"""

import re
import logging


from sqlalchemy import tuple_
from datalayer import queries
from vardb.util import vcfiterator
from vardb.deposit.importers import get_allele_from_record

from vardb.datamodel import sample, user, gene, assessment, allele

from .deposit_from_vcf import DepositFromVCF

log = logging.getLogger(__name__)


class PrefilterBatchGenerator:
    def __init__(self, session, proband_sample_name, generator, prefilter=False, batch_size=2000):
        self.session = session
        self.proband_sample_name = proband_sample_name
        self.prefilter = prefilter
        self.batch_size = batch_size
        self.generator = generator
        self.batch = list()  # Stores the batch to submit
        self.previous_record = None
        self.previous_record_imported = True

    def prefilter_records(self, records):
        """
        Checks whether a record should be prefiltered, i.e. not imported.
        We do this to reduce the amount of data to import for large analyses.

        Current criteria:

        - Not multiallelic for proband
        - GnomAD GENOMES.G > 0.05, num > 5000
        - No existing classifications
        - No variants within +/- 3bp
        """

        result_records = []

        allele_data = [
            (r.variant.CHROM, r.variant.POS, r.variant.REF, r.variant.ALT[0]) for r in records
        ]

        alleles_classifications = (
            self.session.query(
                allele.Allele.chromosome,
                allele.Allele.vcf_pos,
                allele.Allele.vcf_ref,
                allele.Allele.vcf_alt,
            )
            .join(assessment.AlleleAssessment)
            .filter(
                tuple_(
                    allele.Allele.chromosome,
                    allele.Allele.vcf_pos,
                    allele.Allele.vcf_ref,
                    allele.Allele.vcf_alt,
                ).in_(allele_data)
            )
            .distinct()
            .all()
        )

        for idx, r in enumerate(records):
            has_classification = next(
                (
                    a
                    for a in alleles_classifications
                    if a == (r.variant.CHROM, r.variant.POS, r.variant.REF, r.variant.ALT[0])
                ),
                False,
            )
            checks = {
                "non_multiallelic": not r.is_sample_multiallelic(self.proband_sample_name),
                "hi_frequency": float(r.variant.INFO.get("GNOMAD_GENOMES__AF", 0.0)) > 0.05
                and int(r.variant.INFO.get("GNOMAD_GENOMES__AN", 0)) > 5000,
                "position_not_nearby": bool(self.previous_record)
                and not self._is_nearby(self.previous_record, r),
                "no_classification": not has_classification,
            }

            # If current record is nearby previous record, we need to ensure that
            # the previous record also is imported
            if not checks["position_not_nearby"] and not self.previous_record_imported:
                result_records.append(self.previous_record)
            if not all(checks.values()):
                result_records.append(r)
                self.previous_record_imported = True
            else:
                self.previous_record_imported = False

            self.previous_record = r
        return result_records

    @staticmethod
    def _is_nearby(prev, current):
        return (
            abs(prev.variant.POS - current.variant.POS) <= 3
            and prev.variant.CHROM == current.variant.CHROM
        )

    def __next__(self):

        batch = list()
        # We need to look ahead one item due to nearby check,
        # so whole loop is lagging one item
        prev = None
        while True:

            current = next(self.generator, None)
            # None -> generator is empty
            if current is None:
                # If we have loaded any data already,
                # we need to finish processing that
                if prev:
                    batch.append(prev)
                    break

                # No data has been loaded, we're truly done
                if not batch:
                    raise StopIteration()

            # If this was the first value, go straight to loading next
            # since we need both prev and current
            if prev is None:
                prev = current
                continue

            batch.append(prev)

            # Keep loading until we hit batch_size AND the current value is not nearby the previous one
            # AND the current row is not part of a multiallelic site
            is_nearby = prev and self._is_nearby(prev, current)
            prev = current
            if (
                len(batch) >= (self.batch_size - 1)
                and not is_nearby
                and not current.is_multiallelic()
            ):  # Batch size influences no. of db queries
                batch.append(current)
                break

        proband_records = list()
        # We only import variants found in proband
        for record in batch:

            if record.has_allele(self.proband_sample_name):
                proband_records.append(record)

        if self.prefilter:
            prefiltered_records = self.prefilter_records(proband_records)
            return prefiltered_records, batch
        else:
            return proband_records, batch

    def __iter__(self):
        return self


class BlockIterator(object):
    """
    Generates "blocks" of potentially multiallelic records from a batch of records.

    Due to the nature of decomposed + normalized variants, we need to be careful how we
    process the data. Variants belonging to the same sample's genotype can be on different positions
    after decomposition. Example:
    Normal:
    10    ATT A,AG,ATC    0/1 1/2 2/3
    After decompose/normalize:
    10    ATT A   0/1 1/. ./.
    11    TT   G   ./. ./1 1/.
    12    T   C   ./. ./. ./1

    For a Genotype, we want to keep connection to both Alleles (using Genotype.secondallele_id).
    For each sample, if the variant genotype is:
    - '0/0' we don't have any variant, ignore it.
    - '0/1' or '1/1' we can import Genotype directly using a single Allele.
    - '1/.' we need to wait for next './1' entry in order to connect the second Allele.
    """

    def __init__(self, proband_sample_name, sample_names):
        self.proband_sample_name = proband_sample_name
        self.sample_names = sample_names
        self.sample_has_coverage = {s: False for s in sample_names}
        self.proband_alleles = (
            []
        )  # One or two alleles belonging to proband, for creating one genotype
        self.proband_records = (
            []
        )  # One or two records belonging to proband, for creating one genotype
        self.block_records = (
            []
        )  # Stores all records for the whole "block". GenotypeImporter needs some metadata from here.

    def iter_blocks(self, batch, alleles):
        def is_end_of_block(batch, i):
            if i == len(batch) - 1:  # End of batch -> end of block
                return True
            elif not batch[i].is_multiallelic():  # Not on a multiallelic block
                return True
            else:
                # If the next item is on the same multiallelic block, then we need to continue block
                return batch[i].get_block_id() != batch[i + 1].get_block_id()

        for i, record in enumerate(batch):
            add_record_to_block = False
            if record.has_allele(self.proband_sample_name):
                allele = get_allele_from_record(record, alleles)
                # We might have skipped importing the record as allele due to prefiltering
                if allele:
                    self.proband_alleles.append(allele)
                    self.proband_records.append(record)

                add_record_to_block = True

            for sample_name in self.sample_names:

                # Track samples that have no coverage within a multiallelic block
                # './.' often occurs for single records when the sample has genotype in other records,
                # but if it is './.' in _all_ records within a block, it has no coverage at this site
                sample_gt = record.sample_genotype(sample_name)

                if -1 in sample_gt:
                    add_record_to_block = True

                if not all(x == -1 for x in sample_gt):
                    self.sample_has_coverage[sample_name] = True

            if add_record_to_block:
                self.block_records.append(record)

            if is_end_of_block(batch, i):
                if self.proband_records:
                    assert (len(self.proband_records) == 1 and len(self.proband_alleles) == 1) or (
                        len(self.proband_records) == 2 and len(self.proband_alleles) == 2
                    )
                    samples_missing_coverage = [
                        k for k, v in self.sample_has_coverage.items() if not v
                    ]
                    yield self.proband_records, self.proband_alleles, self.block_records, samples_missing_coverage

                # Reset block
                self.block_records = []
                self.proband_records = []
                self.proband_alleles = []
                self.sample_has_coverage = {s: False for s in self.sample_names}

    def finish_check(self):
        assert len(self.proband_alleles) == 0
        assert len(self.proband_records) == 0


class DepositAnalysis(DepositFromVCF):
    def get_usergroup_deposit_config(self, db_analysis):
        """
        Goes through all usergroup configs and searches
        for deposit configuration with match patterns on
        analysis.
        """

        usergroup_configs = (
            self.session.query(user.UserGroup.id, user.UserGroup.config)
            .join(user.UserGroup.genepanels)
            .filter(
                tuple_(gene.Genepanel.name, gene.Genepanel.version)
                == (db_analysis.genepanel_name, db_analysis.genepanel_version)
            )
            .distinct()
            .all()
        )

        matched_configs = []
        for usergroup_id, usergroup_config in usergroup_configs:
            candidate_configs = usergroup_config.get("deposit", {}).get("analysis", [])
            for candidate_config in candidate_configs:
                if re.search(candidate_config["pattern"], db_analysis.name):
                    matched_configs.append((usergroup_id, candidate_config))

        # If multiple configurations match on patterns, raise an exception
        # as we cannot handle the conflict
        if len(matched_configs) > 1:
            exc_text = "Got multiple matching deposit analysis configuration with differing user groups (id, config):\n"
            for m in matched_configs:
                exc_text += "Usergroup id: {}\nConfig: {}\n".format(*m)
            raise RuntimeError(exc_text)

        assert len(matched_configs) <= 1
        return matched_configs[0] if matched_configs else (None, {})

    def postprocess(
        self,
        deposit_usergroup_id,
        deposit_usergroup_config,
        db_analysis,
        db_analysis_interpretation,
    ):
        """
        Postprocessors can be defined in the usergroup configs.

        Example:
        "deposit": {
            "analyses": [
                {
                    "pattern": "^.*",
                    "postprocess": ["analysis_not_ready_warnings"]
                },
                {
                    "pattern": "^SomePattern.*",
                    "postprocess": ["analysis_finalize_without_findings"]
                }
            ]
        }

        """
        if deposit_usergroup_config.get("postprocess"):
            # get_valid_filter_configs() sorts according to user group order,
            # so first is the "default" filter
            filter_config_id = (
                queries.get_valid_filter_configs(self.session, deposit_usergroup_id, db_analysis.id)
                .first()
                .id
            )

            for method in deposit_usergroup_config["postprocess"]:
                # FIXME: circular import, so importing on demand here
                from . import postprocessors

                if method in postprocessors.valid_methods:
                    method_func = getattr(postprocessors, method)
                    method_func(
                        self.session, db_analysis, db_analysis_interpretation, filter_config_id
                    )
                else:
                    # postprocess methods initially defined in fixtures/usergroups.json
                    # then fetched for use from the database
                    pattern = deposit_usergroup_config.get("pattern", "pattern missing")
                    raise RuntimeError(
                        f"Invalid postprocess method {method} in {pattern} of user group {deposit_usergroup_id}"
                    )

    def import_vcf(self, analysis_config_data, append=False):
        """
        Deposit related configs can be defined in the usergroup configs.

        Example:
        "deposit": {
            "analysis": [
                {
                    "pattern": "^.*",
                    "postprocess": ["analysis_not_ready_warnings"],
                    "prefilter": True
                },
                {
                    "pattern": "^SomePattern.*",
                    "postprocess": ["analysis_finalize_without_findings"],
                    "prefilter": False
                }
            ]
        }

        """

        if not append:
            db_genepanel = self.get_genepanel(
                analysis_config_data["genepanel_name"], analysis_config_data["genepanel_version"]
            )
            db_analysis = self.analysis_importer.process(
                analysis_config_data["name"],
                db_genepanel,
                analysis_config_data["report"],
                analysis_config_data["warnings"],
                date_requested=analysis_config_data.get("date_requested"),
            )
            self.session.flush()
        else:
            db_analysis = (
                self.session.query(sample.Analysis)
                .filter(sample.Analysis.name == analysis_config_data["name"])
                .one()
            )

            if any(
                s for s in db_analysis.samples if s.father_id is not None or s.mother_id is not None
            ):
                raise RuntimeError("Appending to a family analysis is not supported.")

        deposit_usergroup_id, deposit_usergroup_config = self.get_usergroup_deposit_config(
            db_analysis
        )

        db_analysis_interpretation = self.analysis_interpretation_importer.process(
            db_analysis, analysis_config_data["priority"], reopen_if_exists=append
        )

        for data in analysis_config_data["data"]:
            vi = vcfiterator.VcfIterator(data["vcf"])

            vcf_sample_names = vi.samples

            log.info("Importing {}".format(db_analysis.name))
            db_samples = self.sample_importer.process(
                vcf_sample_names, db_analysis, sample_type=data["technology"], ped_file=data["ped"]
            )

            if deposit_usergroup_config:
                log.info(
                    "Using deposit configuration from usergroup id {} with pattern {}".format(
                        deposit_usergroup_id, deposit_usergroup_config["pattern"]
                    )
                )
                prefilter = deposit_usergroup_config.get("prefilter")
                log.info("Prefilter: {}".format("Yes" if prefilter else "No"))
                if prefilter:
                    log.info("Prefilter criterias:")
                    log.info("    - GNOMAD_GENOMES.AF > 0.05")
                    log.info("    - GNOMAD_GENOMES.AN > 5000")
                    log.info("    - Nearby variants distance > 3")
                    log.info("    - No existing classifications")
                    log.info(
                        "Postprocess: {}".format(
                            ", ".join(deposit_usergroup_config.get("postprocess", []))
                        )
                    )

            records_count = 0
            imported_records_count = 0

            proband_sample_name = next(s.identifier for s in db_samples if s.proband is True)
            block_iterator = BlockIterator(proband_sample_name, vcf_sample_names)

            prefilter = deposit_usergroup_config.get("prefilter", False)
            # batch_records are _all_ records
            for proband_only_records, batch_records in PrefilterBatchGenerator(
                self.session, proband_sample_name, iter(vi), prefilter=prefilter
            ):
                for record in proband_only_records:
                    self.allele_importer.add(record)
                alleles = self.allele_importer.process()

                for record in proband_only_records:
                    allele = get_allele_from_record(record, alleles)
                    self.annotation_importer.add(record, allele["id"])

                # block_iterator splits batch_records into "multiallelic blocks" (if the site is multiallelic),
                # yielding the proband's records along with data about the other samples used in genotype_importer
                for (
                    proband_records,
                    proband_alleles,
                    block_records,
                    samples_missing_coverage,
                ) in block_iterator.iter_blocks(batch_records, alleles):
                    self.genotype_importer.add(
                        proband_records,
                        proband_alleles,
                        proband_sample_name,
                        db_samples,
                        samples_missing_coverage,
                        block_records,
                    )
                    imported_records_count += len(proband_records)

                annotations = self.annotation_importer.process()
                assert len(alleles) == len(annotations), "Got {} alleles and {} annotations".format(
                    len(alleles), len(annotations)
                )
                self.genotype_importer.process()
                records_count += len(batch_records)
                log.info(
                    "Progress: {} records processed, {} variants imported".format(
                        records_count, imported_records_count
                    )
                )

            # Run asserts on block data
            block_iterator.finish_check()

        if not append:
            self.postprocess(
                deposit_usergroup_id,
                deposit_usergroup_config,
                db_analysis,
                db_analysis_interpretation,
            )

        log.info("All done!")
        return db_analysis
