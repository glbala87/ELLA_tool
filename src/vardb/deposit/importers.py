#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Code for loading the contents of VCF files into the vardb database.

Use one transaction for whole file, and prompts user before committing.
Adds annotation if supplied annotation is different than what is already in db.
Can use specific annotation parsers to split e.g. allele specific annotation.
"""
import base64
import json
import re
import logging
import datetime
from collections import defaultdict

from vardb.datamodel import allele as am, sample as sm, genotype as gm, workflow as wf, assessment
from vardb.datamodel import annotation as annm, assessment as asm
from vardb.util import vcfiterator, annotationconverters
from vardb.deposit.vcfutil import vcfhelper
from vardb.datamodel.user import User

log = logging.getLogger(__name__)


ASSESSMENT_CLASS_FIELD = 'CLASS'
ASSESSMENT_COMMENT_FIELD = 'ASSESSMENT_COMMENT'
ASSESSMENT_DATE_FIELD = 'DATE'
ASSESSMENT_USERNAME_FIELD = 'USERNAME'
REPORT_FIELD = 'REPORT_COMMENT'


def ordered(obj):
    if isinstance(obj, dict):
        return sorted((k, ordered(v)) for k, v in obj.items())
    if isinstance(obj, list):
        return sorted(ordered(x) for x in obj)
    else:
        return obj


def has_diff_ignoring_order(ignore_order_for_key, obj1, obj2):
    csq_1 = obj1.pop(ignore_order_for_key)
    csq_2 = obj2.pop(ignore_order_for_key)
    csq1_ordered = ordered(csq_1)
    csq2_ordered = ordered(csq_2)
    csq_has_diff = not csq1_ordered == csq2_ordered
    if csq_has_diff:
        return True
    else:
        obj1[ignore_order_for_key] = csq1_ordered
        obj2[ignore_order_for_key] = csq2_ordered
        return not obj1 == obj2


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


def is_non_empty_text(input):
    return isinstance(input, basestring) and input


class SampleImporter(object):
    """
    Note: there can be multiple samples with same name in database, and they might differ in genotypes.
    This happens when multiple analyses, using the same sample data in pipeline, is imported.
    They can have been run on different regions.
    """

    def __init__(self, session):
        self.session = session
        self.counter = defaultdict(int)

    def process(self, sample_names, analysis, sample_type='HTS'):
        db_samples = list()
        for sample_idx, sample_name in enumerate(sample_names):
            db_sample = sm.Sample(
                identifier=sample_name,
                sample_type=sample_type,
                analysis=analysis
            )
            db_samples.append(db_sample)
            self.counter['nSamplesAdded'] += 1
        return db_samples

    def get(self, sample_names, analysis):
        db_samples = []
        for sample_name in sample_names:
            db_sample = self.session.query(sm.Sample).filter(
                sm.Sample.identifier == sample_name,
                sm.Sample.analysis == analysis,
            ).all()
            assert len(db_sample) == 1, db_sample
            db_samples += db_sample
        return db_samples


class GenotypeImporter(object):

    ALLELE_DELIMITER = re.compile(r'''[|/]''')  # to split a genotype into alleles

    def __init__(self, session):
        self.session = session
        self.counter = defaultdict(int)
        self.counter['nGenotypeHetroRef'] = 0
        self.counter['nGenotypeHomoNonRef'] = 0
        self.counter['nGenotypeHetroNonRef'] = 0

    def is_sample_het(self, records_sample):
        for record in records_sample:
            gt1, gt2 = GenotypeImporter.ALLELE_DELIMITER.split(record['GT'])
            if gt1 == gt2 == "1":
                return False

        return True

    def should_add_genotype(self, sample):
        """Decide if genotype should be added for this sample

        Only add non-reference called genotypes.
        In other words, don't add if GT = '0/0' or './.'
        """
        gt = [al for al in GenotypeImporter.ALLELE_DELIMITER.split(sample['GT'])]
        return not (gt[0] == gt[1] and gt[0] in ['0', '.'])

    def get_alleles_for_genotypes(self, records_sample, db_alleles):
        """From genotype numbers, return correct objects from alleles list

        Assumes alleles only contain alternative alleles.
        Assume genotype un-phased and returns alleles in reverse-integersorted genotype order (e.g. 0/1 -> 1,0).
        For heterozygous non-ref genootypes, genotype phase is kept.

        If the genotype in the record sample is of the form
        records_sample = [{'GT': '.|1'}, {"GT": '1|.'}], this is interpreted as as GT='2|1',
        and returns db_alleles[1], db_alleles[0]
        """
        # Iterate over records to extract genotype.
        a1 = None
        a2 = None
        for i, record_sample in enumerate(records_sample):
            gt1, gt2 = GenotypeImporter.ALLELE_DELIMITER.split(record_sample['GT'])
            is_unphased = "/" in record_sample["GT"]

            assert gt1 in ['0', '.', '1']
            assert gt2 in ['0', '.', '1']

            if gt1 == "1":
                if is_unphased and a1 is not None:
                    a1,a2 = a2,a1
                assert a1 is None
                a1 = db_alleles[i]

            if gt2 == "1":
                if is_unphased and a2 is not None:
                    a1,a2 = a2,a1
                assert a2 is None
                a2 = db_alleles[i]

        # Flip genotype if given as 0|1
        if a1 is None:
            a1,a2 = a2,a1

        # Second allele should be none if homozygous
        if a1 == a2:
            a2 = None

        return a1, a2

    def process(self, records, sample_name, db_analysis, db_sample, db_alleles):
        records_sample = [record['SAMPLES'][sample_name] for record in records]
        a1, a2 = self.get_alleles_for_genotypes(records_sample, db_alleles)
        if a1 is None:
            assert a2 is None
            return None
        sample_het = self.is_sample_het(records_sample)

        allele_depth = dict()
        for i, record_sample in enumerate(records_sample):
            if record_sample.get('AD'):
                if len(record_sample['AD']) != 2:
                    log.warning("AD not decomposed")
                    continue
                # {'REF': 12, 'A': 134, 'G': 12}
                allele_depth.update({"REF": record_sample["AD"][0]})
                allele_depth.update({k: v for k, v in zip(records[i]['ALT'], record_sample['AD'][1:])})

        # GQ, DP, FILTER, and QUAL should be the same for all decomposed variants
        genotype_quality = records_sample[0].get('GQ')
        sequencing_depth = records_sample[0].get('DP')

        filter = records[0]["FILTER"]
        assert filter == records[0]["FILTER"]

        try:
            qual = int(records[0]['QUAL'])
        except ValueError:
            qual = None

        db_genotype, _ = gm.Genotype.get_or_create(
            self.session,
            allele=a1,
            secondallele=a2,
            homozygous=not sample_het,
            sample=db_sample,
            analysis=db_analysis,
            genotype_quality=genotype_quality,
            sequencing_depth=sequencing_depth,
            variant_quality=qual,
            allele_depth=allele_depth,
            filter_status=filter,
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

        existing = self.session.query(asm.AlleleAssessment).filter(
            asm.AlleleAssessment.allele == allele,
            asm.AlleleAssessment.date_superceeded.is_(None)
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
        """

        if len(db_alleles) > 1:
            raise RuntimeError("Importing assessments is not supported for multiallelic sites")

        db_assessments = list()
        all_info = record['INFO']['ALL']

        class_raw = all_info.get(ASSESSMENT_CLASS_FIELD)
        if not is_non_empty_text(class_raw) or class_raw not in ('1', '2', '3', '4', '5', 'T'):
            logging.warning("Unknown class {}".format(class_raw))
            return

        # Get required fields
        ass_info = {
            'classification': class_raw,
            'evaluation': {'classification': {'comment': 'Comment missing.'}}
        }

        assessment_comment = all_info.get(ASSESSMENT_COMMENT_FIELD)
        if is_non_empty_text(assessment_comment):
            ass_info['evaluation']['classification'].update({'comment': base64.b64decode(assessment_comment).decode('utf-8')})

        user = None
        username_raw = all_info.get(ASSESSMENT_USERNAME_FIELD)
        if is_non_empty_text(username_raw):
            user = self.session.query(User).filter(
                User.username == username_raw
            ).one()
            ass_info['user_id'] = user.id

        allele = db_alleles[0]

        ass_info['date_created'] = datetime.datetime.fromtimestamp(0)  # 1970-00-00 if not proper
        date_raw = all_info.get(ASSESSMENT_DATE_FIELD)
        if is_non_empty_text(date_raw):
            try:
                ass_info['date_created'] = datetime.datetime.strptime(date_raw, '%Y-%m-%d')
            except ValueError:
                pass

        ass_info['genepanel'] = genepanel

        db_assessment = self.create_or_skip_assessment(allele, ass_info)
        if db_assessment:
            if self.session.query(assessment.AlleleReport).filter(
                            assessment.AlleleReport.allele_id == allele.id
            ).count():
                raise RuntimeError("Found an existing allele report, won't create a new one")

            report_data = {'allele_id': allele.id,
                           'user_id': user.id,
                           'alleleassessment_id': db_assessment.id
                           }

            report_raw = all_info.get(REPORT_FIELD)
            if is_non_empty_text(report_raw):
                report_data['evaluation'] = {'comment': base64.b64decode(report_raw).decode('utf-8')}

            report = assessment.AlleleReport(**report_data)
            self.session.add(report)

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
        """
        True if the dictionaries are not identical wrt keys and values.

        Warning: the elements of the list for 'CSQ' might change order
        """

        has_diff = not annos1 == annos2

        if has_diff and 'CSQ' in annos1 and 'CSQ' in annos2:  # sort and compare again:
            return has_diff_ignoring_order('CSQ', annos1, annos2)

        return has_diff

    @staticmethod
    def _compare_transcript(t1, t2):
        # If RefSeq (NM_xxxx.1), ignore the versions.
        # Otherwise, do normal comparison
        if t1.startswith('NM_') and t2.startswith('NM_'):
            return t1.split('.', 1)[0] == t2.split('.', 1)[0]
        return t1 == t2

    def _extract_annotation_from_record(self, record, allele):
        """Given a record, return dict with annotation to be stored in db."""
        # Deep merge 'ALL' annotation and allele specific annotation
        merged_annotation = deepmerge(record['INFO']['ALL'], record['INFO'][allele])

        # Convert the mess of input annotation into database annotation format
        frequencies = dict()
        frequencies.update(annotationconverters.exac_frequencies(merged_annotation))
        frequencies.update(annotationconverters.csq_frequencies(merged_annotation))
        frequencies.update(annotationconverters.indb_frequencies(merged_annotation))

        transcripts = annotationconverters.convert_csq(merged_annotation)
        splice_transcripts = annotationconverters.convert_splice(merged_annotation)
        # Merge splice's transcript objects into the ones from CSQ
        # If refseq transcript, ignore the version when comparing.
        for st in splice_transcripts:
            transcript = next((t for t in transcripts if AnnotationImporter._compare_transcript(t['transcript'], st['transcript'])), None)
            if not transcript:
                transcripts.append(st)
            else:
                # Remove transcript from splice, we use version from CSQ.
                st.pop('transcript')
                transcript.update(st)

        external = dict()
        external.update(annotationconverters.convert_hgmd(merged_annotation))
        external.update(annotationconverters.convert_clinvar(merged_annotation))

        references = annotationconverters.ConvertReferences().process(merged_annotation)

        annotations = {
            'frequencies': frequencies,
            'external': external,
            'prediction': {},
            'transcripts': transcripts,
            'references': references
        }
        return annotations

    def create_or_update_annotation(self, session, db_allele, annotation_data, log=None):
        existing_annotation = self.session.query(annm.Annotation).filter(
            annm.Annotation.allele_id == db_allele.id,
            annm.Annotation.date_superceeded.is_(None)
        ).one_or_none()
        if existing_annotation:
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

    def process(self, record, db_alleles):
        annotations = list()
        alleles = record['ALT']
        for allele, db_allele in zip(alleles, db_alleles):
            annotation_data = self._extract_annotation_from_record(record, allele)
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

            vcf_pos = record["POS"]
            vcf_ref = record["REF"]
            vcf_alt = allele

            allele, _ = am.Allele.get_or_create(
                self.session,
                genome_reference=self.ref_genome,
                chromosome=record['CHROM'],
                start_position=start_pos,
                open_end_position=end_pos,
                change_from=change_from,
                change_to=change_to,
                change_type=change_type,
                vcf_pos=vcf_pos,
                vcf_ref=vcf_ref,
                vcf_alt=vcf_alt
            )
            alleles.append(allele)

            self.counter['nAltAlleles'] += 1
        return alleles


class AnalysisImporter(object):

    def __init__(self, session):
        self.session = session

    def process(self, analysis_name, genepanel):
        """Create analysis with a default gene panel for a sample"""

        if self.session.query(sm.Analysis).filter(
            sm.Analysis.name == analysis_name,
            genepanel == genepanel
        ).count():
            raise RuntimeError("Analysis {} is already imported.".format(analysis_name))

        analysis = sm.Analysis(
            name=analysis_name,
            genepanel=genepanel,
        )
        self.session.add(analysis)
        return analysis

    def get(self, analysis_name, genepanel):
        return self.session.query(sm.Analysis).filter(
            sm.Analysis.name == analysis_name,
            genepanel == genepanel
        ).one()


class AnalysisInterpretationImporter(object):

    def __init__(self, session):
        self.session = session

    def process(self, db_analysis, reopen_if_exists=False):
        existing = self.session.query(wf.AnalysisInterpretation).filter(
            wf.AnalysisInterpretation.analysis_id == db_analysis.id
        ).one_or_none()
        if not existing:
            db_interpretation, _ = wf.AnalysisInterpretation.get_or_create(
                self.session,
                analysis=db_analysis,
                genepanel=db_analysis.genepanel,
                status="Not started"
                )
        else:
            # If the existing is Done, we reopen the analysis since we have added new
            if reopen_if_exists and existing.status == 'Done':
                import api.v1.resources.workflow.helpers as helpers  # TODO: Placed here due to circular imports...
                db_interpretation = helpers.reopen_interpretation(analysis_id=existing.analysis_id)[1]
            else:
                db_interpretation = None
        return db_interpretation


class AlleleInterpretationImporter(object):

    def __init__(self, session):
        self.session = session

    def process(self, genepanel, allele_id):
        db_interpretation, _ = wf.AlleleInterpretation.get_or_create(
            self.session,
            allele_id=allele_id,
            genepanel=genepanel,
            status="Not started"
            )
        return db_interpretation
