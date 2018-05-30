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
import pytz
import itertools
from collections import defaultdict
from sqlalchemy.orm.exc import NoResultFound


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

    @staticmethod
    def parse_ped(ped_file):
        """
        First affected person is assigned as proband.
        """

        def ped_to_sex(value):
            value = value.strip()
            if value == '1':
                return 'Male'
            if value == '2':
                return 'Female'
            return None

        parsed_ped = []
        with open(ped_file) as ped:
            lines = ped.readlines()
            for line in lines:
                if line.startswith('#'):
                    continue
                family_id, sample_id, father_id, mother_id, sex, affected, proband = line.split('\t')
                assert family_id, 'Family ID is empty'
                assert sample_id, 'Sample ID is empty'
                parsed_ped.append({
                    'family_id': family_id.strip(),
                    'sample_id': sample_id.strip(),
                    'father_id': father_id.strip(),
                    'mother_id': mother_id.strip(),
                    'sex': ped_to_sex(sex),
                    'affected': affected.strip() == '2',
                    'proband': proband.strip() == '1'
                })
        return parsed_ped

    def process(self, sample_names, analysis, sample_type='HTS', ped_file=None):

        db_samples = defaultdict(list)  # family_id or None: list of samples

        ped_data = None
        if ped_file:
            ped_data = self.parse_ped(ped_file)
            assert ped_data, 'Provided .ped file yielded no data'
        elif len(sample_names) > 1:
            raise RuntimeError('.ped file required when importing multiple samples')

        # Connect samples to mother and father  {(family_id, sample_id): {'father_id': ..., 'mother_id': ...}}
        to_connect = defaultdict(dict)
        for sample_idx, sample_name in enumerate(sample_names):

            sample_ped_data = {}
            if len(sample_names) == 1:
                sample_ped_data.update({
                    'affected': True,
                    'proband': True
                })

            if ped_data:
                sample_ped_data = next((p for p in ped_data if p['sample_id'] == sample_name), None)
                assert sample_ped_data, "Couldn't find sample name {} in provided .ped file".format(sample_name)

            db_sample = sm.Sample(
                identifier=sample_name,
                sample_type=sample_type,
                analysis=analysis,
                family_id=sample_ped_data.get('family_id'),
                sex=sample_ped_data.get('sex'),
                proband=sample_ped_data.get('proband'),
                affected=sample_ped_data.get('affected'),
            )
            db_samples[sample_ped_data.get('family_id')].append(db_sample)

            if sample_ped_data.get('mother_id') and sample_ped_data.get('mother_id') != '0':
                to_connect[(sample_ped_data.get('family_id'), sample_name)]['mother_id'] = sample_ped_data['mother_id']

            if sample_ped_data.get('father_id') and sample_ped_data.get('father_id') != '0':
                to_connect[(sample_ped_data.get('family_id'), sample_name)]['father_id'] = sample_ped_data['father_id']

            self.session.add(db_sample)
            self.counter['nSamplesAdded'] += 1

        # We need to flush to create ids before we connect them
        self.session.flush()
        for fam_sample_id, values in to_connect.iteritems():
            family_id, sample_id = fam_sample_id
            db_sample = next(s for s in db_samples[family_id] if s.identifier == sample_id)
            if values.get('father_id'):
                db_father = next(s for s in db_samples[family_id] if s.identifier == values['father_id'])
                db_sample.father_id = db_father.id
            if values.get('mother_id'):
                db_mother = next(s for s in db_samples[family_id] if s.identifier == values['mother_id'])
                db_sample.mother_id = db_mother.id

        if ped_file is None:
            assert db_samples.keys() == [None] and len(db_samples[None]) == 1, 'Cannot import multiple samples without pedigree file'

        all_db_samples = list(itertools.chain.from_iterable(db_samples.values()))
        if len(all_db_samples) != len(sample_names):
            self.session.rollback()
            raise RuntimeError("Couldn't import samples to database. (db_samples: %s, vcf_sample_names: %s)" %(str(db_samples), str(vcf_sample_names)))

        proband_count = len([True for s in all_db_samples if s.proband])
        assert proband_count == 1, 'Exactly one sample as proband is required. Got {}.'.format(proband_count)
        father_count = len(set([s.father_id for s in all_db_samples if s.father_id is not None]))
        assert father_count < 2, "An analysis' family can only have one father."
        mother_count = len(set([s.mother_id for s in all_db_samples if s.mother_id is not None]))
        assert mother_count < 2, "An analysis' family can only have one mother."
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

    def __init__(self, session):
        self.session = session

    def is_sample_hom(self, record):
        gt1, gt2 = record['GT'].split('/', 1)
        return gt1 == gt2 == "1"

    def process(self, records, sample_name, db_analysis, db_sample, db_alleles):
        """
        Import genotypes for provided allele(s) for a sample.

        If biallelic site (2 non-reference variants), both records and db_alleles
        will have 2 entries. db_alleles will be connected to allele_id and secondallele_id.

        Phasing is not supported.
        """

        assert len(records) == 1 or len(records) == 2
        assert len(db_alleles) == 1 or len(db_alleles) == 2

        a1 = db_alleles[0]
        a2 = None

        allele_depth = dict()
        for idx, record in enumerate(records):
            record_sample = record['SAMPLES'][sample_name]

            if len(records) == 2:
                assert record_sample['GT'] in ['1/.', './1']

            # Biallelic -> set correct first and second allele
            if record_sample['GT'] == '1/.':
                a1 = db_alleles[idx]
            elif record_sample['GT'] == './1':
                a2 = db_alleles[idx]

            # Update allele depth
            if record_sample.get('AD'):
                if len(record_sample['AD']) == 2:
                    # {'REF': 12, 'A': 134, 'G': 12}
                    allele_depth.update({"REF": record_sample["AD"][0]})
                    allele_depth.update({k: v for k, v in zip(records[idx]['ALT'], record_sample['AD'][1:])})
                else:
                    log.warning("AD not decomposed, allele depth value will be empty")

        # If site is multiallelic, we expect three values for allele depth.
        # However, due to normalization, ALT could be the same for both sites, and the allele depth will only contain two values.
        # Disregard allele depth for these sites
        if a1 is not None and a2 is not None:
            if len(allele_depth) != 3:
                allele_depth = dict()
                log.warning("Unable to extract allele depth. Different REF for the multiallelic site (REF1={}, REF2={})?".format(records[0]['REF'], records[1]['REF']))

        assert a1 != a2

        sample_hom = False
        # If we have multiple records, it's per definition not homozygous
        if len(records) == 1:
            sample_hom = self.is_sample_hom(records[0]['SAMPLES'][sample_name])

        # GQ, DP, FILTER, and QUAL should be the same for all decomposed variants
        genotype_quality = records[0]['SAMPLES'][sample_name].get('GQ')
        sequencing_depth = records[0]['SAMPLES'][sample_name].get('DP')

        filter = records[0]["FILTER"]

        try:
            qual = int(records[0]['QUAL'])
        except ValueError:
            qual = None

        db_genotype, _ = gm.Genotype.get_or_create(
            self.session,
            allele=a1,
            secondallele=a2,
            homozygous=sample_hom,
            sample=db_sample,
            analysis=db_analysis,
            genotype_quality=genotype_quality,
            sequencing_depth=sequencing_depth,
            variant_quality=qual,
            allele_depth=allele_depth,
            filter_status=filter,
        )

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

        annotation = self.session.query(annm.Annotation).filter(
            annm.Annotation.allele == allele,
            annm.Annotation.date_superceeded.is_(None)
        ).one()

        if not existing:
            assessment = asm.AlleleAssessment(**ass_info)
            assessment.allele = allele
            assessment.annotation = annotation
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
        if not is_non_empty_text(class_raw) or class_raw not in ('1', '2', '3', '4', '5', 'U'):
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
            try:
                user = self.session.query(User).filter(
                    User.username == username_raw
                ).one()
                ass_info['user_id'] = user.id
            except NoResultFound, e:
                raise NoResultFound("The user '{}' was not found".format(username_raw), e)

        allele = db_alleles[0]

        date_created = datetime.datetime(1970,1,1, tzinfo=pytz.utc)  # Set to epoch if not proper
        date_raw = all_info.get(ASSESSMENT_DATE_FIELD)
        if is_non_empty_text(date_raw):
            try:
                date_created = datetime.datetime.strptime(date_raw, '%Y-%m-%d')
            except ValueError:
                pass
        ass_info['date_created'] = date_created
        ass_info['genepanel'] = genepanel

        db_assessment = self.create_or_skip_assessment(allele, ass_info)
        if db_assessment:
            if self.session.query(assessment.AlleleReport).filter(
                            assessment.AlleleReport.allele_id == allele.id
            ).count():
                raise RuntimeError("Found an existing allele report, won't create a new one")

            report_data = {'allele_id': allele.id,
                           'user_id': user.id if user else None,
                           'alleleassessment_id': db_assessment.id,
                           'date_created': date_created

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
            return t1.startswith(t2.split('.')[0]) or t2.startswith(t1.split('.')[0])
        return t1 == t2

    def _extract_annotation_from_record(self, record, allele):
        """Given a record, return dict with annotation to be stored in db."""
        # Deep merge 'ALL' annotation and allele specific annotation
        merged_annotation = deepmerge(record['INFO']['ALL'], record['INFO'][allele])

        # Convert the mess of input annotation into database annotation format
        frequencies = dict()
        frequencies.update(annotationconverters.exac_frequencies(merged_annotation))
        frequencies.update(annotationconverters.gnomad_genomes_frequencies(merged_annotation))
        frequencies.update(annotationconverters.gnomad_exomes_frequencies(merged_annotation))
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

    def create_or_update_annotation(self, session, db_allele, annotation_data, update_annotations):
        existing_annotation = self.session.query(annm.Annotation).filter(
            annm.Annotation.allele_id == db_allele.id,
            annm.Annotation.date_superceeded.is_(None)
        ).one_or_none()

        if existing_annotation:
            if not update_annotations:
                return existing_annotation

            if AnnotationImporter.diff_annotation(existing_annotation.annotations, annotation_data):
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

    def process(self, record, db_alleles, update_annotations=True):
        annotations = list()
        alleles = record['ALT']

        for allele, db_allele in zip(alleles, db_alleles):
            annotation_data = self._extract_annotation_from_record(record, allele)
            annotations.append(
                self.create_or_update_annotation(
                    self.session,
                    db_allele,
                    annotation_data,
                    update_annotations
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

    def process(self, analysis_name, priority, genepanel, report, warnings):
        """Create analysis with a default gene panel for a sample"""

        if self.session.query(sm.Analysis).filter(
            sm.Analysis.name == analysis_name,
            genepanel == genepanel
        ).count():
            raise RuntimeError("Analysis {} is already imported.".format(analysis_name))

        analysis = sm.Analysis(
            name=analysis_name,
            genepanel=genepanel,
            priority=priority,
            report=report,
            warnings=warnings
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
        # Get latest interpretation (largest ID), if exists
        existing = self.session.query(wf.AnalysisInterpretation).filter(
            wf.AnalysisInterpretation.analysis_id == db_analysis.id,
        ).order_by(wf.AnalysisInterpretation.id.desc()).limit(1).one_or_none()

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
                db_interpretation = helpers.reopen_interpretation(self.session, analysis_id=existing.analysis_id)[1]
            else:
                db_interpretation = None
        return db_interpretation


class AlleleInterpretationImporter(object):

    def __init__(self, session):
        self.session = session

    def process(self, genepanel, allele_id):
        existing = self.session.query(wf.AlleleInterpretation).filter(
            wf.AlleleInterpretation.allele_id == allele_id,
        ).limit(1).one_or_none()

        if not existing:
            db_interpretation, _ = wf.AlleleInterpretation.get_or_create(
                self.session,
                allele_id=allele_id,
                genepanel=genepanel,
                status="Not started"
                )
        else:
            # Do not create a new interpretation entry if existing
            db_interpretation = None
        return db_interpretation
