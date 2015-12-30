# coding=utf-8
from collections import defaultdict
from api import config


class References(object):

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
            total.extend([e['pmid'] for e in annotation['HGMD']['extrarefs']])
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

        return references


class TranscriptAnnotation(object):
    """
    Fetch out and restructure data that is transcript dependant.
    """

    CSQ_FIELDS = [
        'Consequence',
        'SYMBOL',
        'HGVSc',
        'HGVSp',
        'STRAND',
        'Amino_acids',
        'Existing_variation'
    ]

    SPLICE_FIELDS = [
        'Effect',
        'MaxEntScan-mut',
        'MaxEntScan-wild',
        'pos' # akwardly relevant for for 'de novo' only
    ]


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
            transcripts[transcript_data['Transcript']] = transcript_data

        return transcripts


    def process(self, annotation):

        csq_transcripts = self._csq_transcripts(annotation)
        splice_transcripts = self._splice_transcripts(annotation)


        # Merge transcripts and restructure to list
        transcripts = list()

        for transcript_name in list(set(csq_transcripts.keys() +
                                        splice_transcripts.keys() )):
            t = dict()
            for x in [csq_transcripts,
                      splice_transcripts]:
                t.update(x.get(transcript_name, {}))

            # As CSQ transcripts are treated as master,
            # promote others if CSQ is not available
            if 'Transcript_version' not in t:
                if 'splice_Transcript_version' in t:
                    t['Transcript_version'] = t['splice_Transcript_version']

            transcripts.append(t)

        return sorted(transcripts, key=lambda x: x['Transcript'])


class FrequencyAnnotation(object):

    def _hi_cutoff_in_dataset(self, annotation, dataset):
        if dataset in annotation:
            for freq in config.config['frequencies'][dataset]:
                if freq in annotation[dataset] and \
                   annotation[dataset][freq] >= config.config['acmg']['freq_cutoff_defaults']["hi_freq_cutoff"]:
                    return True
        return False

    def _med_cutoff_in_dataset(self, annotation, dataset):
        if dataset in annotation:
            for freq in config.config['frequencies'][dataset]:
                if freq in annotation[dataset] and \
                   annotation[dataset][freq] < config.config['acmg']['freq_cutoff_defaults']["hi_freq_cutoff"] and \
                   annotation[dataset][freq] >= config.config['acmg']['freq_cutoff_defaults']["lo_freq_cutoff"]:
                    return True
        return False

    def _lo_cutoff_in_dataset(self, annotation, dataset):
        if dataset in annotation:
            for freq in config.config['frequencies'][dataset]:
                if freq in annotation[dataset] and \
                   annotation[dataset][freq] < config.config['acmg']['freq_cutoff_defaults']["lo_freq_cutoff"]:
                    return True
        return False

    def _cutoff_frequencies(self, annotation):
        frequencies = dict()
        frequencies["ExAC_1000G_ESP6500_cutoff"] = "null_freq"
        frequencies["inDB_cutoff"] = "null_freq"

        if not annotation:
            return frequencies

        if (self._hi_cutoff_in_dataset(annotation, "ExAC") or
            self._hi_cutoff_in_dataset(annotation, "1000g") or
            self._hi_cutoff_in_dataset(annotation, "esp6500")):
            frequencies["ExAC_1000G_ESP6500_cutoff"] = "≥hi_freq_cutoff"
        elif (
            self._med_cutoff_in_dataset(annotation, "ExAC") or
            self._med_cutoff_in_dataset(annotation, "1000g") or
            self._med_cutoff_in_dataset(annotation, "esp6500")):
            frequencies["ExAC_1000G_ESP6500_cutoff"] = ["≥lo_freq_cutoff", "<hi_freq_cutoff"]
        elif (
            self._lo_cutoff_in_dataset(annotation, "ExAC") or
            self._lo_cutoff_in_dataset(annotation, "1000g") or
            self._lo_cutoff_in_dataset(annotation, "esp6500")):
            frequencies["ExAC_1000G_ESP6500_cutoff"] = "<lo_freq_cutoff"

        if self._hi_cutoff_in_dataset(annotation, "inDB"):
            frequencies["inDB_cutoff"] = "≥hi_freq_cutoff"
        elif self._med_cutoff_in_dataset(annotation, "inDB"):
            frequencies["inDB_cutoff"] = ["≥lo_freq_cutoff", "<hi_freq_cutoff"]
        elif self._lo_cutoff_in_dataset(annotation, "inDB"):
            frequencies["inDB_cutoff"] = "<lo_freq_cutoff"

        return frequencies

    def _exac_frequencies(self, annotation):
        """
        Manually calculate frequencies from raw ExAC data.
        """

        if 'EXAC' not in annotation:
            return {}

        frequencies = defaultdict(dict)

        count = {}
        num = {}
        hom = {}
        het = {}
        for key, value in annotation['EXAC'].iteritems():
            if 'AC_' in key:
                pop = key.split('AC_')[1]
                assert len(value) == 1
                count[pop] = value[0]
            elif 'AN_' in key:
                pop = key.split('AN_')[1]
                num[pop] = value
            elif 'Hom_' in key:
                hom[key] = value[0]
            elif 'Het_' in key:
                het[key] = value[0]
            elif key == 'AC':
                assert len(value) == 1
                count['G'] = value[0]
            elif key == 'AN':
                num['G'] = value

        for key in count:
            if key in num and num[key]:
                frequencies['ExAC'][key] = float(count[key]) / num[key]

        if hom:
            frequencies['ExAC'].update(hom)
        if het:
            frequencies['ExAC'].update(het)
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

    def process(self, annotation):

        frequencies = self._exac_frequencies(annotation)
        frequencies.update(self._csq_frequencies(annotation))
        frequencies.update(self._indb_frequencies(annotation))
        frequencies.update(self._cutoff_frequencies(frequencies))
        return frequencies

class ExternalAnnotation(object):

    BIC_FIELDS = [
        ('Clinically_Important', lambda x: x.lower())
    ]

    CLINVAR_FIELDS = [
        'CLINSIG',
        'CLNDBN',
        'CLNREVSTAT'
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
        return data


class GeneticAnnotation(object):

    def process(self, annotation):
        pass
        # print annotation.get('RepeatMasker')


class QualityAnnotation(object):

    def process(self, allele):
        if 'genotype' in allele:
            return {
                'QUAL': allele['genotype']['variantQuality'],
                'GQ': allele['genotype']['genotypeQuality'],
                'DP': allele['genotype']['sequencingDepth'],
                'FILTER': allele['genotype']['filterStatus']
            }
        else:
            return {}


class AnnotationProcessor(object):

    @staticmethod
    def process(allele):
        """
        Creates/converts annotation data from input Allele dictionary data.
        """

        native_annotations = allele['annotation']['annotations']
        data = {
            'transcripts': TranscriptAnnotation().process(native_annotations),
            'frequencies': FrequencyAnnotation().process(native_annotations),
            'references': References().process(native_annotations),
            'genetic': GeneticAnnotation().process(native_annotations),
            'external': ExternalAnnotation().process(native_annotations),
            'quality': QualityAnnotation().process(allele)
        }

        return data
