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
                                    HGMDInfoProcessor, \
                                    SplitToDictInfoProcessor, AlleleInterpretationImporter, \
                                    batch_generator

from vardb.datamodel import sample, workflow, user, gene

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

    def postprocess(self, db_analysis, db_analysis_interpretation):
        """
        Postprocessors can be defined in the usergroup configs.

        Example:
        "deposit": {
            "postprocess": [
                {
                    "name": "^.*",
                    "type": "analysis",
                    "methods": ["analysis_not_ready_findings"]
                },
                {
                    "name": "^SomePattern.*",
                    "type": "analysis",
                    "methods": ["analysis_finalize_without_findings"]
                }
            ]
        }

        """

        usergroup_configs = self.session.query(
            user.UserGroup.id,
            user.UserGroup.config
        ).join(
            user.UserGroup.genepanels
        ).filter(
            tuple_(gene.Genepanel.name, gene.Genepanel.version) == (db_analysis.genepanel_name, db_analysis.genepanel_version)
        ).all()

        for usergroup_id, usergroup_config in usergroup_configs:
            candidate_processors = usergroup_config.get('deposit', {}).get('postprocess', [])
            if not candidate_processors:
                continue

            filter_config_id = self.session.query(sample.FilterConfig.id).join(
                user.UserGroup
            ).filter(
                user.UserGroup.id == usergroup_id,
                sample.FilterConfig.default.is_(True)
            ).scalar()

            for c in candidate_processors:
                if re.search(c['name'], db_analysis.name):

                    for method in c['methods']:
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

        vi = vcfiterator.VcfIterator(analysis_config_data.vcf_path)
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
        records_count = 0
        imported_records_count = 0
        for batch_records in batch_generator(vi.iter, batch_size):

            # First import batch as alleles
            for record in batch_records:

                # if not self.is_inside_transcripts(record, db_genepanel):
                #     error = "The following variant is not inside the genepanel %s\n" % (db_genepanel.name + "_" + db_genepanel.version)
                #     error += "%s\t%s\t%s\t%s\t%s\n" % (record["CHROM"], record["POS"], record["ID"], record["REF"], ",".join(record["ALT"]))
                #     raise RuntimeError(error)

                # If a non-multialleleic site for proband, check against import filter.
                # FIXME: Check number > 5000 for filtering
                # if record['SAMPLES'][proband_sample_name]['GT'] in ['0/1', '1/1']:
                #    if 'GNOMAD_GENOMES' in record['INFO']['ALL'] and record['INFO']['ALL']['GNOMAD_GENOMES']['AF'][0] > 0.2:
                #        continue

                # We only import variants found in proband
                if record['SAMPLES'][proband_sample_name]['GT'] in VARIANT_GENOTYPES:
                    self.allele_importer.add(record)
                else:
                    continue

            alleles = self.allele_importer.process()

            # Process batch again to import annotation and genotypes (which both needs allele ids)
            for record in batch_records:

                if record['SAMPLES'][proband_sample_name]['GT'] in VARIANT_GENOTYPES:
                    allele = self.get_allele_from_record(record, alleles)
                    # We might have skipped importing the record as allele due to import filtering
                    if not allele:
                        continue

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
            self.postprocess(db_analysis, db_analysis_interpretation)

        log.info('All done, committing')
        self.session.commit()
