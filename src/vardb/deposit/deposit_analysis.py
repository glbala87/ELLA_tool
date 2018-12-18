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
from collections import OrderedDict, defaultdict


import jsonschema
from sqlalchemy import tuple_
from vardb.util import DB, vcfiterator
from vardb.deposit.importers import (
    AnalysisImporter,
    AnnotationImporter,
    SampleImporter,
    GenotypeImporter,
    AlleleImporter,
    AnalysisInterpretationImporter,
    HGMDInfoProcessor,
    SplitToDictInfoProcessor,
    AlleleInterpretationImporter,
    batch_generator,
    get_allele_from_record,
)

from vardb.datamodel import sample, workflow, user, gene, assessment, allele
from vardb.datamodel.jsonschemas import load_schema

from deposit_from_vcf import DepositFromVCF

log = logging.getLogger(__name__)


VARIANT_GENOTYPES = ["0/1", "1/.", "./1", "1/1"]


def import_filterconfigs(session, filterconfigs):
    result = {"updated": 0, "created": 0}
    filter_config_schema = load_schema("filterconfig.json")

    for filterconfig in filterconfigs:
        jsonschema.validate(filterconfig, filter_config_schema)
        filterconfig = dict(filterconfig)
        usergroup_name = filterconfig.pop("usergroup")
        usergroup_id = (
            session.query(user.UserGroup.id).filter(user.UserGroup.name == usergroup_name).scalar()
        )

        filterconfig["usergroup_id"] = usergroup_id

        existing = (
            session.query(sample.FilterConfig)
            .filter(
                sample.FilterConfig.usergroup_id == usergroup_id,
                sample.FilterConfig.name == filterconfig["name"],
            )
            .one_or_none()
        )

        if existing:
            for k, v in filterconfig.iteritems():
                setattr(existing, k, v)
            result["updated"] += 1
        else:
            fc = sample.FilterConfig(**filterconfig)
            session.add(fc)
            result["created"] += 1
    return result


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

        allele_data = [(r["CHROM"], r["POS"], r["REF"], r["ALT"][0]) for r in records]

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
                    if a == (r["CHROM"], r["POS"], r["REF"], r["ALT"][0])
                ),
                False,
            )
            checks = {
                "non_multiallelic": r["SAMPLES"][self.proband_sample_name]["GT"] in ["0/1", "1/1"],
                "hi_frequency": "GNOMAD_GENOMES" in r["INFO"]["ALL"]
                and r["INFO"]["ALL"]["GNOMAD_GENOMES"]["AF"][0] > 0.05
                and r["INFO"]["ALL"]["GNOMAD_GENOMES"]["AN"] > 5000,
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
        return abs(prev["POS"] - current["POS"]) <= 3 and prev["CHROM"] == current["CHROM"]

    def next(self):

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
            is_nearby = prev and self._is_nearby(prev, current)
            prev = current
            if (
                len(batch) >= (self.batch_size - 1) and not is_nearby
            ):  # Batch size influences no. of db queries
                batch.append(current)
                break

        proband_records = list()
        # We only import variants found in proband
        for record in batch:
            if record["SAMPLES"][self.proband_sample_name]["GT"] in VARIANT_GENOTYPES:
                proband_records.append(record)

        if self.prefilter:
            prefiltered_records = self.prefilter_records(proband_records)
            return prefiltered_records, batch
        else:
            return proband_records, batch

    def __iter__(self):
        return self


class MultiAllelicBlockIterator(object):
    """
    Generates "blocks" of multiallelic records from a batch of records.

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
        self.needs_secondallele = {s: False for s in sample_names}
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
        for record in batch:
            add_record_to_block = False
            if record["SAMPLES"][self.proband_sample_name]["GT"] in VARIANT_GENOTYPES:

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
                sample_gt = record["SAMPLES"][sample_name]["GT"]
                if "." in sample_gt:
                    add_record_to_block = True

                if sample_gt != "./.":
                    self.sample_has_coverage[sample_name] = True

                if sample_gt in ["1/.", "./1"]:
                    self.needs_secondallele[sample_name] = not self.needs_secondallele[sample_name]

            if add_record_to_block:
                self.block_records.append(record)

            if not any(self.needs_secondallele.values()):
                if self.proband_records:
                    assert (len(self.proband_records) == 1 and len(self.proband_alleles) == 1) or (
                        len(self.proband_records) == 2 and len(self.proband_alleles) == 2
                    )
                    samples_missing_coverage = [
                        k for k, v in self.sample_has_coverage.iteritems() if not v
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
                    "postprocess": ["analysis_not_ready_findings"]
                },
                {
                    "pattern": "^SomePattern.*",
                    "postprocess": ["analysis_finalize_without_findings"]
                }
            ]
        }

        """
        if deposit_usergroup_config.get("postprocess"):

            filter_config_id = (
                self.session.query(sample.FilterConfig.id)
                .join(user.UserGroup)
                .filter(
                    user.UserGroup.id == deposit_usergroup_id, sample.FilterConfig.default.is_(True)
                )
                .scalar()
            )

            for method in deposit_usergroup_config["postprocess"]:
                if method == "analysis_not_ready_findings":
                    from .postprocessors import (
                        analysis_not_ready_findings,
                    )  # FIXME: Has circular import, so must import here...

                    analysis_not_ready_findings(
                        self.session, db_analysis, db_analysis_interpretation, filter_config_id
                    )

                elif method == "analysis_finalize_without_findings":
                    from .postprocessors import (
                        analysis_finalize_without_findings,
                    )  # FIXME: Has circular import, so must import here...

                    analysis_finalize_without_findings(
                        self.session, db_analysis, db_analysis_interpretation, filter_config_id
                    )

    def import_vcf(self, analysis_config_data, sample_type="HTS", append=False):
        """
        Deposit related configs can be defined in the usergroup configs.

        Example:
        "deposit": {
            "analysis": [
                {
                    "pattern": "^.*",
                    "postprocess": ["analysis_not_ready_findings"],
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

        vi = vcfiterator.VcfIterator(analysis_config_data.vcf_path)
        vi.addInfoProcessor(HGMDInfoProcessor(vi.getMeta()))
        vi.addInfoProcessor(SplitToDictInfoProcessor(vi.getMeta()))

        vcf_sample_names = vi.samples

        db_genepanel = self.get_genepanel(
            analysis_config_data.gp_name, analysis_config_data.gp_version
        )

        if not append:
            db_analysis = self.analysis_importer.process(
                analysis_config_data.analysis_name,
                db_genepanel,
                analysis_config_data.report,
                analysis_config_data.warnings,
                date_requested=analysis_config_data.date_requested,
            )
        else:
            db_analysis = (
                self.session.query(sample.Analysis)
                .filter(sample.Analysis.name == analysis_config_data.analysis_name)
                .one()
            )

            if any(
                s for s in db_analysis.samples if s.father_id is not None or s.mother_id is not None
            ):
                raise RuntimeError("Appending to a family analysis is not supported.")

        log.info("Importing {}".format(db_analysis.name))
        db_analysis_interpretation = self.analysis_interpretation_importer.process(
            db_analysis, analysis_config_data.priority, reopen_if_exists=append
        )
        db_samples = self.sample_importer.process(
            vcf_sample_names,
            db_analysis,
            sample_type=sample_type,
            ped_file=analysis_config_data.ped_path,
        )

        deposit_usergroup_id, deposit_usergroup_config = self.get_usergroup_deposit_config(
            db_analysis
        )
        if deposit_usergroup_config:
            log.info(
                "Using deposit configuration from usergroup id {} with pattern {}".format(
                    deposit_usergroup_id, deposit_usergroup_config["pattern"]
                )
            )
            log.info(
                "Prefilter: {}".format("Yes" if deposit_usergroup_config.get("prefilter") else "No")
            )
            log.info("Prefilter criterias:")
            log.info("    - GNOMAD_GENOMES.AF > 0.05")
            log.info("    - GNOMAD_GENOMES.AN > 5000")
            log.info("    - Nearby variants distance > 3")
            log.info("    - No existing classifications")
            log.info(
                "Postprocess: {}".format(", ".join(deposit_usergroup_config.get("postprocess", [])))
            )

        records_count = 0
        imported_records_count = 0

        proband_sample_name = next(s.identifier for s in db_samples if s.proband is True)
        block_iterator = MultiAllelicBlockIterator(proband_sample_name, vcf_sample_names)

        prefilter = deposit_usergroup_config.get("prefilter", False)
        # prefiltered_records are proband-only, filtered records
        # batch_records are _all_ records
        for prefiltered_records, batch_records in PrefilterBatchGenerator(
            self.session, proband_sample_name, vi.iter(), prefilter=prefilter
        ):
            for record in prefiltered_records:
                self.allele_importer.add(record)
            alleles = self.allele_importer.process()

            for record in prefiltered_records:
                allele = get_allele_from_record(record, alleles)
                self.annotation_importer.add(record, allele["id"])

            # block_iterator splits batch_records into "multiallelic blocks",
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
            genotypes, genotypesamplesdata = self.genotype_importer.process()
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

        log.info("All done, committing")
        self.session.commit()
