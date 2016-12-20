#!/usr/bin/env python
"""
Code for loading the contents of VCF files into the vardb database.

Use one transaction for whole file, and prompts user before committing.
Adds annotation if supplied annotation is different than what is already in db.
Can use specific annotation parsers to split e.g. allele specific annotation.
"""

import sys
import argparse
import re
import json
import itertools
import logging
import datetime
from collections import defaultdict

from sqlalchemy import and_
import sqlalchemy.orm.exc

import vardb.datamodel
from vardb.datamodel import allele as am, sample as sm, genotype as gm, workflow as wf
from vardb.datamodel import annotation as annm, assessment as asm
from vardb.datamodel import gene
from vardb.util import vcfiterator
from vardb.deposit.vcfutil import vcfhelper


log = logging.getLogger(__name__)


ASSESSMENT_CLASS_FIELD = 'class'
ASSESSMENT_COMMENT_FIELD = 'ASSC'


def deepmerge(source, destination):
    """
    Deepmerge dicts.
    http://stackoverflow.com/a/20666342

    >>> a = { 'first' : { 'all_rows' : { 'pass' : 'dog', 'number' : '1' } } }
    >>> b = { 'first' : { 'all_rows' : { 'fail' : 'cat', 'number' : '5' } } }
    >>> merge(b, a) == { 'first' : { 'all_rows' : { 'pass' : 'dog', 'fail' : 'cat', 'number' : '5' } } }
    True
    """
    for key, value in source.items():
        if isinstance(value, dict):
            # get node or create one
            node = destination.setdefault(key, {})
            deepmerge(value, node)
        else:
            destination[key] = value

    return destination


class SampleImporter(object):
    """
    Note: there can be multiple samples with same name in database, and they might differ in genotypes.
    This happens when multiple analyses, using the same sample data in pipeline, is imported.
    They can have been run on different regions.
    """

    def __init__(self, session):
        self.session = session
        self.counter = defaultdict(int)

    def process(self, sample_names, sample_configs=None):
        db_samples = list()
        sample_type = 'HTS'  # TODO: Agree on values for Sample.sampleType enums and get from sample_config
        if sample_configs:
            assert isinstance(sample_names, list)
            assert isinstance(sample_configs, list)
            assert len(sample_names) == len(sample_configs)
        for sample_idx, sample_name in enumerate(sample_names):
            db_sample = sm.Sample(
                identifier=sample_name,
                sample_type=sample_type,
                deposit_date=datetime.datetime.now(),
                sample_config=sample_configs[sample_idx] if sample_configs else None
                )
            db_samples.append(db_sample)
            self.counter['nSamplesAdded'] += 1
        return db_samples


class GenotypeImporter(object):

    ALLELE_DELIMITER = re.compile(r'''[|/]''')  # to split a genotype into alleles

    def __init__(self, session):
        self.session = session
        self.counter = defaultdict(int)
        self.counter['nGenotypeHetroRef'] = 0
        self.counter['nGenotypeHomoNonRef'] = 0
        self.counter['nGenotypeHetroNonRef'] = 0

    def is_sample_het(self, record_sample):
        gt1, gt2 = GenotypeImporter.ALLELE_DELIMITER.split(record_sample['GT'])
        return gt1 != gt2

    def should_add_genotype(self, sample):
        """Decide if genotype should be added for this sample

        Only add non-reference called genotypes.
        In other words, don't add if GT = '0/0' or './.'
        """
        gt = [al for al in GenotypeImporter.ALLELE_DELIMITER.split(sample['GT'])]
        return not (gt[0] == gt[1] and gt[0] in ['0', '.'])

    def get_alleles_for_genotypes(self, record_sample, db_alleles):
        """From genotype numbers, return correct objects from alleles list

        Assumes alleles only contain alternative alleles.
        Assume genotype un-phased and returns alleles in reverse-integersorted genotype order (e.g. 0/1 -> 1,0).
        """
        # Must define sort order for genotypes so alleles come in a defined order
        # and alternative alleles come before ref (alt comes as gt1).
        gt1, gt2 = sorted((int(g) for g in GenotypeImporter.ALLELE_DELIMITER.split(record_sample['GT'])), reverse=True)
        assert gt1 > 0

        a1 = db_alleles[gt1 - 1]

        # Only use a2 if hetrozygous non-reference
        if gt1 != gt2 and gt2 != 0:
            a2 = db_alleles[gt2 - 1]
        else:
            a2 = None
        return a1, a2

    def process(self, record, sample_name, db_analysis, db_sample, db_alleles):
        record_sample = record['SAMPLES'][sample_name]
        a1, a2 = self.get_alleles_for_genotypes(record_sample, db_alleles)
        sample_het = self.is_sample_het(record_sample)

        try:
            qual = int(record['QUAL'])
        except ValueError:
            qual = None

        allele_depth = dict()
        if record_sample.get('AD'):
            # {'A': 134, 'G': 12}
            allele_depth = {k: v for k,v in zip([record['REF']] + record['ALT'], record_sample['AD'])}

        db_genotype, _ = gm.Genotype.get_or_create(
            self.session,
            allele=a1,
            secondallele=a2,
            homozygous=not sample_het,
            sample=db_sample,
            analysis=db_analysis,
            genotype_quality=record_sample.get('GQ'),
            sequencing_depth=record_sample.get('DP'),
            variant_quality=qual,
            allele_depth=allele_depth,
            filter_status=record['FILTER'],
            vcf_pos=record['POS'],
            vcf_ref=record['REF'],
            vcf_alt=','.join(record['ALT'])
        )
        if sample_het and a2 is None: self.counter["nGenotypeHetroRef"] += 1
        elif not sample_het and a2 is None: self.counter["nGenotypeHomoNonRef"] += 1
        elif sample_het and a2 is not None: self.counter["nGenotypeHetroNonRef"] += 1
        return db_genotype


class AssessmentImporter(object):

    def __init__(self, session):
        self.session = session
        self.counter = defaultdict(int)
        self.counter.update({
            'nNovelAssessments': 0,
            'nAssessmentsUpdated': 0
        })

    def create_or_skip_assessment(self, allele, ass_info):
        """
        Create an assessment for allele if it doesn't exist already
        """

        # Imported assessments are set as outdated by default
        ass_info['dateLastUpdate'] = datetime.datetime.min

        existing = self.session.query(asm.AlleleAssessment).filter(
            asm.AlleleAssessment.allele == allele,
            asm.AlleleAssessment.date_superceeded == None
        ).first()

        if not existing:
            assessment = asm.AlleleAssessment(**ass_info)
            assessment.allele = allele
            self.session.add(assessment)
            self.counter["nNovelAssessments"] += 1
            return assessment
        else:
            log.warning("Assessment for {} already exists, skipping!".format(str(allele)))
            return None

    def process(self, record, db_alleles, assess_class=None, genepanel=None):
        """
        Add assessment of allele if present.

        If one field is present, we require all of them to avoid incomplete assessments.
        Sets assessment status to 1 (curated), but sets dateLastUpdate to
        datetime.datetime.min (i.e. year 1) to demand re-assessment of variant.
        """

        db_assessments = list()
        all_info = record['INFO']['ALL']

        # Get required fields
        ass_info = {
            'classification': all_info.get(ASSESSMENT_CLASS_FIELD),
            'evaluation': {'classification': {'comment': all_info.get(ASSESSMENT_COMMENT_FIELD)}}
        }

        # If no fields are specified, don't insert anything to db
        if all(v is None for v in ass_info.values()):
            return db_assessments

        if any(v is None for v in ass_info.values()):
            raise RuntimeError("All fields ({}) are required for importing an assessment".format(
                ', '.join([ASSESSMENT_CLASS_FIELD,
                           ASSESSMENT_COMMENT_FIELD]
                          )))

        if len(db_alleles) > 1:
            raise RuntimeError("Importing assessments is not supported for multiallelic sites")

        allele = db_alleles[0]

        ass_info['dateLastUpdate'] = datetime.datetime.min
        ass_info['genepanel'] = genepanel
        db_assessment = self.create_or_skip_assessment(allele, ass_info)
        if db_assessment:
            self.counter['nAssessmentsUpdated'] += 1
            db_assessments.append(db_assessment)
        return db_assessments


class SplitToDictInfoProcessor(vcfiterator.BaseInfoProcessor):
    """
    For use with VcfIterator
    Splits keys like HGMD__HGMDMUT_key{n} to a dictionary:
    {
        'HGMD': {
            'HGMDMUT': {
                'key1': value
                'key2': value
            }
        }
    }
    """

    def __init__(self, meta):
        self.meta = meta

    def accepts(self, key, value, processed):
        if processed:
            return False
        return '__' in key

    def process(self, key, value, info_data, alleles, processed):
        keys = key.split('__')
        func = self.getConvertFunction(self.meta, key)

        node = info_data['ALL']
        # Create or search nested structure
        while keys:
            k = keys.pop(0)
            new_node = node.get(k)
            if new_node is None:
                node[k] = dict()
                if keys:
                    node = node[k]
            else:
                node = new_node
        # Insert value on inner node (dict)
        if isinstance(value, basestring):
            value = vcfhelper.translate_to_original(value)
            node[k] = func(value)
        else:
            node[k] = value


class HGMDInfoProcessor(SplitToDictInfoProcessor):
    """
    Processes HGMD data, specifically parsing the extrarefs data into a list.

    Builds on top of SplitToDictInfoProcessor, since it's a special case of same functionality.
    """

    def __init__(self, meta):
        self.meta = meta
        self.fields = self._parseFormat()

    def _parseFormat(self):

        field = next((e for e in self.meta['INFO'] if e['ID'] == 'HGMD__extrarefs'), None)
        if not field:
            return None
        fields = field['Description'].split('(')[1].split(')')[0].split('|')
        return fields

    def accepts(self, key, value, processed):
        if key.startswith('HGMD__'):
            return True

    def _parseExtraRef(self, value):
        entries = [dict(zip(self.fields, [vcfhelper.translate_to_original(e) for e in v.split('|')])) for v in value.split(',')]
        for e in entries:
            for t in ['pmid']:
                if e.get(t):
                    try:
                        e[t] = int(e[t])
                    # If value is not int, it's not valid pmid. Remove key from data.
                    except ValueError:
                        del e[t]
            for k, v in dict(e).iteritems():
                if v == '':
                    del e[k]
        return entries

    def process(self, key, value, info_data, alleles, processed):
        section, hgmd_key = key.split('__', 1)
        # Process data using SplitToDictInfoProcessor
        super(HGMDInfoProcessor, self).process(key, value, info_data, alleles, processed)

        # Now our data should be in info_dict['ALL']['HGMD']
        # If the key is extrarefs, we overwrite it with the parsed version
        if self.fields:
            if hgmd_key == 'extrarefs':
                info_data['ALL'][section]['extrarefs'] = self._parseExtraRef(value)
        elif hgmd_key == 'pmid':
            info_data['ALL'][section]['pmid'] = int(info_data['ALL'][section]['pmid'])


class SpliceInfoProcessor(vcfiterator.BaseInfoProcessor):
    """
    Processes Splice data.

    Typical ##INFO header:
     - ##INFO=<ID=splice,Number=1,Type=String,Description="Splice effect. Format: Transcript|Effect|MaxEntScan-wild|MaxEntScan-mut|MaxEntScan-closest|dist">

    Typical INFO field:
     - splice=NM_000059|consensus_not_affected|6.1|6.1
     - splice=NM_000059|predicted_lost|8.35|0.0&NM_000059|splice_donor_variant
     - splice=NM_000059|consensus_not_affected|9.79|9.79&NM_000059|de_novo|1.47|3.32|9.79|49

    Several effects are combined with '&'
    """

    field = 'splice'

    def __init__(self, meta):
        self.meta = meta
        self.fields = self._parseFormat()

    def _parseFormat(self):
        field = next((e for e in self.meta['INFO'] if e['ID'] == SpliceInfoProcessor.field), None)
        if not field:
            return None
        fields = field['Description'].split('Format: ', 1)[1].split('|')
        return fields

    def accepts(self, key, value, processed):
        if not self.fields:
            return False
        return key == SpliceInfoProcessor.field

    def process(self, key, value, info_data, alleles, processed):
        data = []
        for effect in value.split('&'):
            d = {k: v for k, v in zip(self.fields, effect.split('|')) if not v == ''}
            data.append(d)
        info_data['ALL'][key] = data


class inDBInfoProcessor(vcfiterator.BaseInfoProcessor):
    """
    Processes inDB data.
    """

    def __init__(self, meta):
        self.meta = meta
        self.processors = {
            'inDB__inDB_filter': lambda x: x,
            'inDB__inDB_indications': self._split_to_dict_factory(int),
            'inDB__inDB_alleleFreq': self._split_to_dict_factory(float),
            'inDB__inDB_genotypeFreq': self._split_to_dict_factory(float),
            'inDB__inDB_noMutInd': lambda x: int(x)
        }

    def _split_to_dict_factory(self, func):

        def split_to_dict(value):
            result = dict()
            for entry in value.split(','):
                key_value = entry.split(':')
                if key_value:
                    result[key_value[0]] = func(key_value[1])
            return result

        return split_to_dict

    def accepts(self, key, value, processed):
        return key in self.processors

    def process(self, key, value, info_data, alleles, processed):
        if 'inDB' not in info_data['ALL']:
            info_data['ALL']['inDB'] = dict()

        data = self.processors[key](value)

        # Put alleleFreq into allele specific keys
        if key == 'inDB__inDB_alleleFreq':
            for allele in alleles:
                if allele in data:
                    info_data[allele]['inDB'] = {'alleleFreq': data[allele]}
        else:
            name = key.split('__inDB_')[1]
            info_data['ALL']['inDB'][name] = data


class AnnotationImporter(object):

    def __init__(self, session):
        self.session = session
        self.counter = defaultdict(int)
        self.counter.update({
            'nNovelAnnotation': 0,
            'nUpdatedAnnotation': 0,
            'nNoChangeAnnotation': 0
        })

    @staticmethod
    def diff_annotation(annos1, annos2):
        """True if the dictionaries are not identical wrt keys and values."""

        # TODO: Verify functionality!
        if not annos1 == annos2:
            return True
        else:
            return False

    def _extract_annotation_from_record(self, record, allele, skip_anno=None):
        """Given a record, return dict with annotation to be stored in db.

            Uses VCF Info and ID fields. Skip if tag is self.skip_anno.
        """
        annotations = {}
        # Deep merge 'ALL' annotation and allele specific annotation
        merged_annotation = deepmerge(record['INFO']['ALL'], record['INFO'][allele])
        for key, value in merged_annotation.iteritems():
            if skip_anno and key in self.skip_anno:
                continue
            else:
                annotations[key] = value
        assert "id" not in annotations, "VCF (Info) already includes 'id' field!"
        annotations["id"] = record['ID'] if not record['ID'] is None else str()
        return annotations

    def create_or_update_annotation(self, session, db_allele, annotation_data, log=None):
        annotations = self.session.query(annm.Annotation).filter(
            annm.Annotation.allele_id == db_allele.id,
            annm.Annotation.date_superceeded == None
        ).all()
        if annotations:
            assert len(annotations) == 1
            existing_annotation = annotations[0]
            if self.diff_annotation(existing_annotation.annotations, annotation_data):
                # Replace existing annotation
                existing_annotation.date_superceeded = datetime.datetime.now()
                annotation, _ = annm.Annotation.get_or_create(
                    self.session,
                    allele=db_allele,
                    annotations=annotation_data,
                    previous_annotation=existing_annotation
                )
                self.counter["nUpdatedAnnotation"] += 1
            else:  # Keep existing annotation
                self.counter["nNoChangeAnnotation"] += 1

        else:  # Create new
            existing_annotation, _ = annm.Annotation.get_or_create(
                self.session,
                allele=db_allele,
                annotations=annotation_data
            )
            self.counter["nNovelAnnotation"] += 1

        return existing_annotation

    def process(self, record, db_alleles, skip_anno=None):
        annotations = list()
        alleles = record['ALT']
        for allele, db_allele in zip(alleles, db_alleles):
            annotation_data = self._extract_annotation_from_record(record, allele, skip_anno=None)
            annotations.append(
                self.create_or_update_annotation(
                    self.session,
                    db_allele,
                    annotation_data,
                    AnnotationImporter.diff_annotation
                )
            )

        return annotations


class AlleleImporter(object):

    def __init__(self, session, ref_genome="GRCh37"):
        self.session = session
        self.ref_genome = ref_genome
        self.counter = defaultdict(int)

    def process(self, record):
        """
        Add or update alleles for record.

        Returns the alleles for this record as datamodel.Allele objects.
        """
        alleles = list()
        for allele_no, allele in enumerate(record['ALT']):
            start_offset, allele_length, change_type, change_from, change_to = \
                vcfhelper.compare_alleles(record['REF'], allele)
            start_pos = vcfhelper.get_start_position(record['POS'], start_offset, change_type)
            end_pos = vcfhelper.get_end_position(record['POS'], start_offset, allele_length)
            allele, _ = am.Allele.get_or_create(
                self.session,
                genome_reference=self.ref_genome,
                chromosome=record['CHROM'],
                start_position=start_pos,
                open_end_position=end_pos,
                change_from=change_from,
                change_to=change_to,
                change_type=change_type
            )
            alleles.append(allele)

            self.counter['nAltAlleles'] += 1
        return alleles


class AnalysisImporter(object):

    def __init__(self, session):
        self.session = session

    def process(self, db_samples, analysis_config, genepanel):
        """Create analysis with a default gene panel for a sample"""

        if self.session.query(sm.Analysis).filter(
            sm.Analysis.name == analysis_config['name'],
            genepanel == genepanel
        ).count():
            raise RuntimeError("Analysis {} is already imported.".format(analysis_config['name']))

        analysis = sm.Analysis(
            name=analysis_config['name'],
            samples=db_samples,
            genepanel=genepanel,
            analysis_config=analysis_config
        )
        self.session.add(analysis)
        return analysis


class AnalysisInterpretationImporter(object):

    def __init__(self, session):
        self.session = session

    def process(self, db_analysis):
        db_interpretation, _ = wf.AnalysisInterpretation.get_or_create(
            self.session,
            analysis=db_analysis,
            genepanel=db_analysis.genepanel,
            status="Not started"
            )
        return db_interpretation


