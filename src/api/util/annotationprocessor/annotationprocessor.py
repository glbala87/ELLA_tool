# -*- coding: utf-8 -*-

from collections import defaultdict
import re

from api import config
from genepanelprocessor import GenepanelCutoffsAnnotationProcessor
from vardb.datamodel.gene import Transcript


class References(object):
    CONTRIBUTION_KEY = 'references'

    def _csq_pubmeds(self, annotation):
        if 'CSQ' not in annotation:
            return list()
        # Get first elem which has PUBMED ids (it's the same in all elements)
        pubmed_data = next((d['PUBMED'] for d in annotation['CSQ'] if 'PUBMED' in d), list())
        return pubmed_data

    def _hgmd_pubmeds(self, annotation):
        if 'HGMD' not in annotation:
            return list()

        total = list()
        if 'pmid' in annotation['HGMD']:
            total.append(annotation['HGMD']['pmid'])
        if 'extrarefs' in annotation['HGMD']:
            total.extend([e['pmid'] for e in annotation['HGMD']['extrarefs'] if 'pmid' in e])
        return total

    def process(self, annotation):

        csq_pubmeds = self._csq_pubmeds(annotation)
        hgmd_pubmeds = self._hgmd_pubmeds(annotation)

        # Merge references and restructure to list
        references = list()
        common_pmid = set(csq_pubmeds) & set(hgmd_pubmeds)
        for common in common_pmid:
            references.append({
                'pubmedID': common, 'sources': ['VEP', 'HGMD']
            })

        for pmid in [p for p in csq_pubmeds if p not in common_pmid]:
            references.append({
                'pubmedID': pmid,
                'sources': ['VEP']
            })

        for pmid in [p for p in hgmd_pubmeds if p not in common_pmid]:
            references.append({
                'pubmedID': pmid,
                'sources': ['HGMD']
            })

        return {References.CONTRIBUTION_KEY: references}


class TranscriptAnnotation(object):
    """
    Fetch out and restructure data that is transcript dependant.
    """

    CONTRIBUTION_KEY = 'transcripts'
    CONTRIBUTION_KEY_FILTERED_TRANSCRIPTS = 'filtered_transcripts'

    # Matches NM_007294.3:c.4535-213G>T  (gives ['-', '213'])
    # but not NM_007294.3:c.4535G>T
    INTRON_CHECK_REGEX = re.compile(r'.*c\.[0-9]+?(?P<plus_minus>[\-\+])(?P<distance>[0-9]+)')

    CSQ_FIELDS = [
        'Consequence',
        'SYMBOL',
        'HGVSc',
        'HGVSp',
        'STRAND',
        'Amino_acids',
        'Existing_variation',
        'EXON',
        'INTRON',
        'Codons'
    ]

    SPLICE_FIELDS = [
        'Effect',
        'MaxEntScan-mut',
        'MaxEntScan-wild',
        'MaxEntScan-closest',  # relevant for 'de novo'
        'dist'  # relevant for 'de novo'
    ]

    def __init__(self, config):
        self.config = config

    def _get_transcript_intronic(self, transcript_data):
        """
        Checks whether variant for given transcript is considered
        intronic according to coordinates given by configuration.

        Checks first if consequence is intron_variant,
        then parses the cDNA coordinates to check how far into
        the intron it is.
        """
        criteria = self.config.get('variant_criteria', {}).get('intronic_region')
        if criteria and 'intron_variant' in transcript_data['Consequence']:
            hgvsc = transcript_data.get('HGVSc')
            match = re.match(TranscriptAnnotation.INTRON_CHECK_REGEX, hgvsc)
            if match:
                match_data = match.groupdict()

                # Regex should guarantee int conversion is possible
                plus_minus, distance = match_data['plus_minus'], int(match_data['distance'])

                # Check if distance is outside criteria
                if plus_minus in criteria:
                    return distance > criteria[plus_minus]

        return False

    def _get_is_last_exon(self, transcript_data):

        exon = transcript_data.get('EXON')
        if exon:
            parts = exon.split('/')
            return parts[0] == parts[1]
        return False

    def _get_worst_consequence(self, transcripts):
        """
        Finds the transcript with the worst consequence.
        :param transcripts: List of transcripts with data
        :return: List of transcript names with the worst consequence.
        """
        if not self.config.get('transcripts', {}).get('consequences'):
            return list()

        # Get minimum index for each item (since each have several consequences), then sort by that index
        consequences = self.config['transcripts']['consequences']

        def sort_func(x):
            if 'Consequence' in x and x['Consequence']:
                return min(consequences.index(c) for c in x['Consequence'])
            else:
                return 9999999
        sorted_transcripts = sorted(transcripts, key=sort_func)

        worst_consequence = sorted_transcripts[0]['Consequence']
        worst_consequences = list()
        for t in sorted_transcripts:
            if any(c in t.get('Consequence', []) for c in worst_consequence):
                worst_consequences.append(t['Transcript'])
            else:
                break

        return worst_consequences

    def _csq_transcripts(self, annotation):
        if 'CSQ' not in annotation:
            return dict()

        transcripts = dict()

        # Invert CSQ data to map to transcripts
        for data in annotation['CSQ']:
            # Filter out non-transcripts and non-refseq transcripts
            if data.get('Feature_type') != 'Transcript' or \
               not any(data['Feature'].startswith(x) for x in ['NM', 'NR', 'XM']):
                continue

            transcript_data = {k: data[k] for k in TranscriptAnnotation.CSQ_FIELDS if k in data}
            # VEP transcript versions are treated as master version
            transcript_data['Transcript'], transcript_data['Transcript_version'] = data['Feature'].split('.', 1)

            # Only keep dbSNP data (e.g. rs123456789)
            if 'Existing_variation' in transcript_data:
                transcript_data['Existing_variation'] = [t for t in transcript_data['Existing_variation']
                                                         if t.startswith('rs')]

            # Add custom types
            if 'HGVSc' in transcript_data:
                # Split away transcript part
                transcript_data['HGVSc_short'] = transcript_data['HGVSc'].split(':', 1)[1]
            if 'HGVSp' in transcript_data:
                transcript_data['HGVSp_short'] = transcript_data['HGVSp'].split(':', 1)[1]
            is_last_exon = self._get_is_last_exon(transcript_data)
            transcript_data['in_last_exon'] = 'yes' if is_last_exon else 'no'
            transcripts[transcript_data['Transcript']] = transcript_data
        return transcripts


    def _splice_transcripts(self, annotation):
        if 'splice' not in annotation:
            return dict()

        transcripts = dict()

        for data in annotation['splice']:
            if 'Transcript' not in data:
                continue

            transcript_data = {'splice_' + k.replace('-', '_'): data[k] for k in TranscriptAnnotation.SPLICE_FIELDS if k in data}
            transcript_data['Transcript'], transcript_data['splice_Transcript_version'] = data['Transcript'].split('.', 1)

            if transcript_data['Transcript'] in transcripts:
                transcripts[transcript_data['Transcript']].append(transcript_data)
            else:
                transcripts[transcript_data['Transcript']] = [transcript_data]

        return transcripts

    @staticmethod
    def get_genepanel_transcripts(transcript_names, genepanel):
        """
        Searches input transcripts for matching transcript names in the genepanel,
        and returns the list of matches. If no matches are done, returns all RefSeq
        transcripts.

        *The transcript version is stripped off during matching.*

        :param transcript_names: List of transcript names (without version) to search for
        :param genepanel:
        :type genepanel: vardb.datamodel.gene.Genepanel
        :return: list of genepanel transcript names, without version: ['NM_13423', ...]
        """

        transcript_names = [Transcript.get_name(t) for t in transcript_names]

        gp_transcripts = list()
        for transcript in genepanel.transcripts:
            gp_transcripts.append(transcript.refseqName)
            gp_transcripts.append(transcript.ensemblID)  # TODO: necessary to add ensembleId as well?

        transcript_names_in_genepanel = [Transcript.get_name(t) for t in gp_transcripts]

        return list(set(transcript_names).intersection(set(transcript_names_in_genepanel)))

    def process(self, annotation, genepanel=None):
        """
        :param annotation
        :param genepanel: If provided, adds filtered_transcript to output,
                          containing the name of the transcripts found in
                          genepanel.
        :type genepanel: vardb.datamodel.gene.Genepanel
        """
        csq_transcripts = self._csq_transcripts(annotation)
        splice_transcripts = self._splice_transcripts(annotation)

        # Merge transcripts and restructure to list
        transcripts = list()

        for transcript_name in list(set(csq_transcripts.keys() +
                                        splice_transcripts.keys())):

            t = dict()
            for x in [csq_transcripts]:
                t.update(x.get(transcript_name, {}))
            for x in [splice_transcripts]:
                t['Splice'] = x.get(transcript_name, [])

            # As CSQ transcripts are treated as master,
            # promote others if CSQ is not available
            if 'Transcript_version' not in t:
                if ('Splice' in t) and (len(t['Splice'])) and ('splice_Transcript_version' in t['Splice'][0]):
                        t['Transcript_version'] = t['Splice'][0]['splice_Transcript_version']

            transcripts.append(t)

        final_transcripts = sorted(transcripts, key=lambda x: x['Transcript'])

        # Add 'intronic' flag:
        for t in final_transcripts:
            t['intronic'] = self._get_transcript_intronic(t)

        result = {TranscriptAnnotation.CONTRIBUTION_KEY: final_transcripts}

        if genepanel:
            final_transcript_names = [t['Transcript'] for t in final_transcripts]
            result[TranscriptAnnotation.CONTRIBUTION_KEY_FILTERED_TRANSCRIPTS] \
                = TranscriptAnnotation.get_genepanel_transcripts(final_transcript_names, genepanel)

        result['worst_consequence'] = self._get_worst_consequence(final_transcripts)
        return result


class FrequencyAnnotation(object):
    CONTRIBUTION_KEY='frequencies'

    def __init__(self, config, genepanel=None):
        self.config = config
        self.genepanel = genepanel

    def _exac_frequencies(self, annotation):
        """
        Manually calculate frequencies from raw ExAC data.

        :param: annotation: a dict with key 'EXAC'
        :returns: dict with key 'ExAC'
        """

        if 'EXAC' not in annotation:
            return {}

        frequencies = defaultdict(dict)

        count = {}
        num = {}
        hom = {}
        het = {}
        for key, value in annotation['EXAC'].iteritems():
            # Be careful if rearranging!
            if key == 'AC':
                assert len(value) == 1
                count['G'] = value[0]
            elif key == 'AC_Het':
                assert len(value) == 1
                het['G'] = value[0]
            elif key == 'AC_Hom':
                assert len(value) == 1
                hom['G'] = value[0]
            elif key == 'AN':
                num['G'] = value
            elif key.startswith('AC_'):
                pop = key.split('AC_')[1]
                assert len(value) == 1
                count[pop] = value[0]
            elif key.startswith('AN_'):
                pop = key.split('AN_')[1]
                num[pop] = value
            elif key.startswith('Hom_'):
                pop = key.split('Hom_')[1]
                hom[pop] = value[0]
            elif key.startswith('Het_'):
                pop = key.split('Het_')[1]
                het[pop] = value[0]

        for key in count:
            if key in num and num[key]:
                frequencies['ExAC'][key] = float(count[key]) / num[key]

        if hom:
            frequencies['ExAC'].update({'hom': hom})
        if het:
            frequencies['ExAC'].update({'het': het})
        if num:
            frequencies['ExAC'].update({'num': num})
        if count:
            frequencies['ExAC'].update({'count': count})

        return dict(frequencies)

    def _csq_frequencies(self, annotation):
        if 'CSQ' not in annotation:
            return {}

        # Get first elem which has frequency data (it's the same in all elements)
        frequencies = dict()
        freq_data = next((d for d in annotation['CSQ'] if any('MAF' in k for k in d)), None)
        if freq_data:
            # Check whether the allele provided for the frequency is the same as the one we have in our allele.
            # VEP gives minor allele for some fields, which can be the reference instead of the allele
            processed = {
                k.replace('_MAF', '').replace('MAF', ''): v[freq_data['Allele']]
                for k, v in freq_data.iteritems()
                if 'MAF' in k and
                freq_data['Allele'] in v
            }
            if processed:
                # ESP6500 freqs
                esp6500_freq = dict()
                for f in ['AA', 'EA']:
                    if f in processed:
                        esp6500_freq[f] = processed.pop(f)
                if esp6500_freq:
                    frequencies['esp6500'] = esp6500_freq

                if processed:
                    frequencies['1000g'] = processed
        return dict(frequencies)

    def _indb_frequencies(self, annotation):
        if 'inDB' not in annotation:
            return {}

        return {'inDB': annotation['inDB']}

    def process(self, annotation, symbol=None, genepanel=None):
        """

        :param annotation:
        :param symbol: the gene symbol
        :param genepanel:
        :type genepanel: vardb.datamodel.gene.Genepanel
        :return:
        """
        processor = GenepanelCutoffsAnnotationProcessor(self.config, genepanel)
        frequencies = self._exac_frequencies(annotation)
        frequencies.update(self._csq_frequencies(annotation))
        frequencies.update(self._indb_frequencies(annotation))
        frequencies.update(processor.cutoff_frequencies(frequencies, symbol))

        return {FrequencyAnnotation.CONTRIBUTION_KEY: frequencies}


class ExternalAnnotation(object):
    CONTRIBUTION_KEY = 'external'

    BIC_FIELDS = [
        ('Clinically_Important', lambda x: x.lower())
    ]

    CLINVAR_FIELDS = [
        'CLNSIG',
        'CLNDBN',
        'CLNREVSTAT',
        'CLNACC'
    ]

    HGMD_FIELDS = [
        'acc_num',
        'codon',
        'disease',
        'tag',
    ]

    def _bic(self, annotation):
        if 'BIC' not in annotation:
            return dict()

        # Assumption: BRCA1 and BRCA2 data don't overlap
        assert len(annotation['BIC']) < 2
        if annotation.get('BIC'):
            # Should just be one key (either 'BRCA1' or 'BRCA2')
            # we just return the data
            bic_data = annotation['BIC'][annotation['BIC'].keys()[0]]
            data = {'BIC': {k[0]: k[1](bic_data[k[0]]) for k in ExternalAnnotation.BIC_FIELDS if k[0] in bic_data}}
            return data
        return {}

    def _clinvar(self, annotation):
        if 'CLINVAR' not in annotation:
            return dict()

        data = {k: annotation['CLINVAR'][k] for k in ExternalAnnotation.CLINVAR_FIELDS if k in annotation['CLINVAR']}
        return {'CLINVAR': data}

    def _hgmd(self, annotation):
        if 'HGMD' not in annotation:
            return dict()

        data = {k: annotation['HGMD'][k] for k in ExternalAnnotation.HGMD_FIELDS if k in annotation['HGMD']}
        return {'HGMD': data}

    def process(self, annotation):
        data = dict()

        data.update(self._bic(annotation))
        data.update(self._clinvar(annotation))
        data.update(self._hgmd(annotation))
        return {ExternalAnnotation.CONTRIBUTION_KEY: data}


class GeneticAnnotation(object):

    def process(self, annotation):
        return {}
        # print annotation.get('RepeatMasker')


class QualityAnnotation(object):
    CONTRIBUTION_KEY='quality'

    def process(self, genotype):
        data = {
            'QUAL': genotype.get('variantQuality'),
            'GQ': genotype.get('genotypeQuality'),
            'DP': genotype.get('sequencingDepth'),
            'FILTER': genotype.get('filterStatus'),
            'AD': genotype.get('alleleDepth')
        }
        return {QualityAnnotation.CONTRIBUTION_KEY: data}


def find_symbol(annotation):
    transcripts = annotation.get(TranscriptAnnotation.CONTRIBUTION_KEY, None)
    filtered_transcripts = annotation.get(TranscriptAnnotation.CONTRIBUTION_KEY_FILTERED_TRANSCRIPTS, None)

    # filtered contains only the refSeq ID, must find full transcript:
    found = None
    if filtered_transcripts and len(filtered_transcripts) > 0:
        look_for = filtered_transcripts[0]
        found = filter(lambda t: t['Transcript'] == look_for, transcripts)

    # prefer filtered transcripts:
    symbols = map(lambda t: t['SYMBOL'], found if found else transcripts)

    if len(set(symbols)) > 1:
        raise Exception("The transcript(s) selected don't have the same gene symbol, found genes {}"
                        .format(','.join(list(set(symbols)))))

    return symbols.pop()


class AnnotationProcessor(object):

    @staticmethod
    def process(annotation, custom_annotation=None, genotype=None, genepanel=None):
        """
        Creates/converts annotation data from input Allele dictionary data.

        :param annotation:
        :param custom_annotation:
        :param genotype:
        :param genepanel:
        :type genepanel: vardb.datamodel.gene.Genepanel
        :return: a dict with one key for each "class" of annotation: 'transcripts', 'frequency', 'references'
        'external', 'quality' (only if genotype)
        """

        data = dict()
        data.update(TranscriptAnnotation(config.config).process(annotation, genepanel=genepanel))
        gene_symbol = find_symbol(data)
        data.update(FrequencyAnnotation(config.config).process(annotation, symbol=gene_symbol, genepanel=genepanel))
        data.update(References().process(annotation))
        data.update(GeneticAnnotation().process(annotation))
        data.update(ExternalAnnotation().process(annotation))

        if custom_annotation:
            # Merge/overwrite data with custom_annotation
            for key in config.config['custom_annotation'].keys():
                if key in custom_annotation:
                    if key not in data:
                        data[key] = dict()
                    data[key].update(custom_annotation[key])

            # References are merged specially
            if 'references' in data and 'references' in custom_annotation:
                data['references'] = data['references'] + custom_annotation['references']

        if genotype:
            data.update(QualityAnnotation().process(genotype))

        return data
