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


from sqlalchemy import tuple_
from vardb.util import DB, vcfiterator
from vardb.deposit.importers import AnalysisImporter, AnnotationImporter, SampleImporter, \
                                    GenotypeImporter, AlleleImporter, AnalysisInterpretationImporter, \
                                    SpliceInfoProcessor, HGMDInfoProcessor, \
                                    SplitToDictInfoProcessor, AlleleInterpretationImporter, \
                                    batch_generator

from vardb.datamodel import sample, workflow, user, gene, assessment, allele

from deposit_from_vcf import DepositFromVCF

log = logging.getLogger(__name__)


VARIANT_GENOTYPES = ['0/1', '1/.', './1', '1/1']


def import_filterconfigs(session, filterconfigs):
    result = {
        'updated': 0,
        'created': 0
    }
    for filterconfig in filterconfigs:
        filterconfig = dict(filterconfig)
        usergroup_name = filterconfig.pop('usergroup')
        usergroup_id = session.query(user.UserGroup.id).filter(
            user.UserGroup.name == usergroup_name
        ).scalar()

        filterconfig['usergroup_id'] = usergroup_id

        existing = session.query(sample.FilterConfig).filter(
            sample.FilterConfig.usergroup_id == usergroup_id,
            sample.FilterConfig.name == filterconfig['name']
        ).one_or_none()

        if existing:
            for k, v in filterconfig.iteritems():
                setattr(existing, k, v)
            result['updated'] += 1
        else:
            fc = sample.FilterConfig(**filterconfig)
            session.add(fc)
            result['created'] += 1
    return result


class DepositAnalysis(DepositFromVCF):

    def get_usergroup_deposit_config(self, db_analysis):
        """
        Goes through all usergroup configs and searches
        for deposit configuration with match patterns on
        analysis.
        """

        usergroup_configs = self.session.query(
            user.UserGroup.id,
            user.UserGroup.config
        ).join(
            user.UserGroup.genepanels
        ).filter(
            tuple_(gene.Genepanel.name, gene.Genepanel.version) == (db_analysis.genepanel_name, db_analysis.genepanel_version)
        ).all()

        matched_configs = []
        for usergroup_id, usergroup_config in usergroup_configs:
            candidate_configs = usergroup_config.get('deposit', {}).get('analysis', [])
            for candidate_config in candidate_configs:
                if re.search(candidate_config['pattern'], db_analysis.name):
                    matched_configs.append((usergroup_id, candidate_config))

        # If multiple configurations match on patterns, raise an exception
        # as we cannot handle the conflict
        if len(matched_configs) > 1:
            exc_text = "Got multiple matching deposit analysis configuration with differing user groups (id, config):\n"
            for m in matched_configs:
                exc_text += 'Usergroup id: {}\nConfig: {}\n'.format(*m)
            raise RuntimeError(exc_text)

        assert len(matched_configs) <= 1
        return matched_configs[0] if matched_configs else (None, {})

    def prefilter_records(self, records, proband_sample_name, previous_batch_last_record, previous_batch_last_record_imported):
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
        previous_record = previous_batch_last_record
        previous_record_imported = previous_batch_last_record_imported

        allele_data = [
            (r['CHROM'], r['POS'], r['REF'], r['ALT'][0]) for r in records
        ]

        alleles_classifications = self.session.query(
            allele.Allele.chromosome,
            allele.Allele.vcf_pos,
            allele.Allele.vcf_ref,
            allele.Allele.vcf_alt
        ).join(
            assessment.AlleleAssessment
        ).filter(
            tuple_(
                allele.Allele.chromosome,
                allele.Allele.vcf_pos,
                allele.Allele.vcf_ref,
                allele.Allele.vcf_alt
            ).in_(allele_data)
        ).distinct().all()

        for r in records:
            has_classification = next(
                (a == (r['CHROM'], r['POS'], r['REF'], r['ALT'][0]) for a in alleles_classifications),
                False
            )
            checks = {
                'non_multiallelic': r['SAMPLES'][proband_sample_name]['GT'] in ['0/1', '1/1'],
                'hi_frequency': 'GNOMAD_GENOMES' in r['INFO']['ALL'] and
                                r['INFO']['ALL']['GNOMAD_GENOMES']['AF'][0] > 0.05 and
                                r['INFO']['ALL']['GNOMAD_GENOMES']['AN'] > 5000,
                'position_not_nearby': bool(previous_record) and (abs(r['POS'] - previous_record['POS']) > 3 or r['CHROM'] != previous_record['CHROM']),
                'no_classification': not has_classification
            }
            # If current record is nearby previous record, we need to ensure that
            # the previous record also is imported
            if not checks['position_not_nearby'] and not previous_record_imported:
                result_records.append(previous_record)

            if not all(checks.values()):
                result_records.append(r)
                previous_record_imported = True
            else:
                previous_record_imported = False

            previous_record = r

        return result_records, previous_record_imported

    def postprocess(self, deposit_usergroup_id, deposit_usergroup_config, db_analysis, db_analysis_interpretation):
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
        if deposit_usergroup_config.get('postprocess'):

            filter_config_id = self.session.query(sample.FilterConfig.id).join(
                user.UserGroup
            ).filter(
                user.UserGroup.id == deposit_usergroup_id,
                sample.FilterConfig.default.is_(True)
            ).scalar()

            for method in deposit_usergroup_config['postprocess']:
                if method == 'analysis_not_ready_findings':
                    from .postprocessors import analysis_not_ready_findings  # FIXME: Has circular import, so must import here...
                    analysis_not_ready_findings(
                        self.session,
                        db_analysis,
                        db_analysis_interpretation,
                        filter_config_id
                    )

                elif method == 'analysis_finalize_without_findings':
                    from .postprocessors import analysis_finalize_without_findings  # FIXME: Has circular import, so must import here...
                    analysis_finalize_without_findings(
                        self.session,
                        db_analysis,
                        db_analysis_interpretation,
                        filter_config_id
                    )

    def import_vcf(self, analysis_config_data, batch_size=1000, sample_type="HTS", append=False):
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
        vi.addInfoProcessor(SpliceInfoProcessor(vi.getMeta()))
        vi.addInfoProcessor(HGMDInfoProcessor(vi.getMeta()))
        vi.addInfoProcessor(SplitToDictInfoProcessor(vi.getMeta()))

        vcf_sample_names = vi.samples

        db_genepanel = self.get_genepanel(analysis_config_data.gp_name, analysis_config_data.gp_version)

        if not append:
            db_analysis = self.analysis_importer.process(
                analysis_config_data.analysis_name,
                db_genepanel,
                analysis_config_data.report,
                analysis_config_data.warnings,
                date_requested=analysis_config_data.date_requested
            )
        else:
            db_analysis = self.session.query(sample.Analysis).filter(
                sample.Analysis.name == analysis_config_data.analysis_name
            ).one()

            if any(s for s in db_analysis.samples if s.father_id is not None or s.mother_id is not None):
                raise RuntimeError("Appending to a family analysis is not supported.")

        log.info("Importing {}".format(db_analysis.name))
        db_analysis_interpretation = self.analysis_interpretation_importer.process(
            db_analysis,
            analysis_config_data.priority,
            reopen_if_exists=append
        )
        db_samples = self.sample_importer.process(
            vcf_sample_names,
            db_analysis,
            sample_type=sample_type,
            ped_file=analysis_config_data.ped_path
        )

        deposit_usergroup_id, deposit_usergroup_config = self.get_usergroup_deposit_config(db_analysis)
        if deposit_usergroup_config:
            log.info("Using deposit configuration from usergroup id {} with pattern {}".format(deposit_usergroup_id, deposit_usergroup_config['pattern']))
            log.info("Prefilter: {}".format('Yes' if deposit_usergroup_config.get('prefilter') else 'No'))
            log.info("Postprocess: {}".format(', '.join(deposit_usergroup_config.get('postprocess', []))))

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
        proband_alleles = []  # One or two alleles belonging to proband, for creating one genotype
        proband_records = []  # One or two records belonging to proband, for creating one genotype
        block_records = []  # Stores all records for the whole "block". GenotypeImporter needs some metadata from here.
        previous_batch_last_record = None  # Stores the last record of the previous batch, used in prefilter function
        previous_batch_last_record_imported = False  # Indicates whether last record in previous batch was imported
        records_count = 0
        imported_records_count = 0

        for batch_records in batch_generator(vi.iter, batch_size):

            # First fetch the records we want
            processed_records = []
            for record in batch_records:

                # if not self.is_inside_transcripts(record, db_genepanel):
                #     error = "The following variant is not inside the genepanel %s\n" % (db_genepanel.name + "_" + db_genepanel.version)
                #     error += "%s\t%s\t%s\t%s\t%s\n" % (record["CHROM"], record["POS"], record["ID"], record["REF"], ",".join(record["ALT"]))
                #     raise RuntimeError(error)

                # We only import variants found in proband
                if record['SAMPLES'][proband_sample_name]['GT'] in VARIANT_GENOTYPES:
                    processed_records.append(record)
                else:
                    continue

            if deposit_usergroup_config.get('prefilter'):
                prefiltered_records, previous_batch_last_record_imported = self.prefilter_records(
                    processed_records,
                    proband_sample_name,
                    previous_batch_last_record
                )
                previous_batch_last_record = processed_records[-1]
                processed_records = prefiltered_records

            for record in processed_records:
                self.allele_importer.add(record)
            alleles = self.allele_importer.process()

            # Process batch again to import annotation and genotypes (which both needs allele ids)
            # We need to process the original batch_records and not processed_records, since
            # we also use data from the non-proband and prefiltered variants
            for record in batch_records:

                if record['SAMPLES'][proband_sample_name]['GT'] in VARIANT_GENOTYPES:

                    allele = self.get_allele_from_record(record, alleles)
                    # We might have skipped importing the record as allele due to prefiltering
                    if allele:
                        # Annotation
                        self.annotation_importer.add(record, allele['id'])
                        proband_alleles.append(allele)
                        proband_records.append(record)

                    block_records.append(record)

                elif any(needs_secondallele.values()):
                    block_records.append(record)

                for sample_name in vcf_sample_names:
                    # Track samples that have no coverage within a multiallelic block
                    # './.' often occurs for single records when the sample has genotype in other records,
                    # but if it is './.' in _all_ records within a block, it has no coverage at this site
                    sample_gt = record['SAMPLES'][sample_name]['GT']
                    if sample_gt != './.':
                        sample_has_coverage[sample_name] = True

                    if sample_gt in ['1/.', './1']:
                        needs_secondallele[sample_name] = not needs_secondallele[sample_name]

                # Genotype
                # Run this always, since a "block" can be finished on records with no proband data
                if not any(needs_secondallele.values()):
                    if proband_records:
                        assert len(proband_alleles) == len(proband_records)
                        samples_missing_coverage = [k for k, v in sample_has_coverage.iteritems() if not v]
                        self.genotype_importer.add(
                            proband_records,
                            proband_alleles,
                            proband_sample_name,
                            db_samples,
                            samples_missing_coverage,
                            block_records
                        )
                        sample_has_coverage = {s: False for s in vcf_sample_names}
                        imported_records_count += len(proband_records)
                        proband_alleles = []
                        proband_records = []

                    # Block is finished
                    block_records = []

            annotations = self.annotation_importer.process()
            assert len(alleles) == len(annotations), 'Got {} alleles and {} annotations'.format(len(alleles), len(annotations))

            genotypes, genotypesamplesdata = self.genotype_importer.process()
            records_count += len(batch_records)
            log.info("Progress: {} records processed, {} variants imported".format(records_count, imported_records_count))

        assert len(proband_alleles) == 0
        assert len(proband_records) == 0

        if not append:
            self.postprocess(
                deposit_usergroup_id,
                deposit_usergroup_config,
                db_analysis,
                db_analysis_interpretation
            )

        log.info('All done, committing')
        self.session.commit()
