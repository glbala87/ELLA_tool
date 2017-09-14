# coding=utf-8
import unittest
import pytest

from .. import annotationconverters
from .. import GNOMAD_EXOMES_RESULT_KEY, GNOMAD_EXOMES_ANNOTATION_KEY
from .. import GNOMAD_GENOMES_RESULT_KEY, GNOMAD_GENOMES_ANNOTATION_KEY
from .. import EXAC_RESULT_KEY, EXAC_ANNOTATION_KEY

class TestReferences():

    def test_get_pubmeds_HGMD(self):
        data = {
            'HGMD': {
                'pmid': 1,
                'extrarefs': [
                    {
                        'pmid': 2
                    },
                    {
                        'pmid': 3
                    },
                ]
            },

        }

        pubmeds = annotationconverters.ConvertReferences().process(data)
        assert pubmeds[0] == {
                'pubmed_id': 1,
                'sources': ['HGMD'],
                'source_info': {"HGMD": "Primary literature report. No comments."},
            }

        assert pubmeds[1] == {
                'pubmed_id': 2,
                'sources': ['HGMD'],
                'source_info': {'HGMD': "Reftag not specified. No comments."},
            }

        assert pubmeds[2] == {
                'pubmed_id': 3,
                'sources': ['HGMD'],
                'source_info': {'HGMD': "Reftag not specified. No comments."},
            }


class TestFrequencyAnnotation():

    def test_csq_no_gmaf(self):
        """
        Don't include GMAF if given for the REF allele only.
        """

        data = {
            'CSQ': [
                {
                    'GMAF': {
                        'C': 0.122
                    },
                    'SAS_MAF': {
                        'G': 0.123
                    },
                    'Allele': 'G'
                }
            ]

        }
        freq = annotationconverters.csq_frequencies(data)
        assert 'GMAF' not in freq['1000g']['freq']

    def test_frequency_strip_maf_from_name(self):
        """
        Don't include MAF part of name
        """
        data = {
            'CSQ': [
                {
                    'GMAF': {
                        'G': 0.122
                    },
                    'EUR_MAF': {
                        'G': 0.123
                    },
                    'Allele': 'G'
                },
                {}
            ]

        }
        freq = annotationconverters.csq_frequencies(data)
        assert 'G' in freq['1000g']['freq']
        assert 'GMAF' not in freq['1000g']['freq']
        assert 'EUR' in freq['1000g']['freq']
        assert 'EUR_MAF' not in freq['1000g']['freq']

    def test_exac_conversion(self):
        annotation_source = {
            EXAC_ANNOTATION_KEY: {
                'AC_TEST': [13],
                'AN_TEST': 2,
                'AC_ZERO': [0],
                'AN_ZERO': 0
            }
        }

        converted = annotationconverters.exac_frequencies(annotation_source)[EXAC_RESULT_KEY]
        assert 'TEST' in converted['freq']
        assert float(13)/2 == converted['freq']['TEST']
        assert 'ZERO' not in converted['freq']

    def test_gnomad_exomes_conversion(self):

        annotation_source = {
            GNOMAD_EXOMES_ANNOTATION_KEY: {
                'AC_TEST': [13],
                'AN_TEST': 2,
                'AC_ZERO': [0],
                'AN_ZERO': 0
            }
        }

        converted = annotationconverters.gnomad_exomes_frequencies(annotation_source)[GNOMAD_EXOMES_RESULT_KEY]
        assert 'TEST' in converted['freq']
        assert float(13)/2 == converted['freq']['TEST']
        assert 'ZERO' not in converted['freq']

    def test_gnomad_genomes_conversion(self):

        annotation_source = {
            GNOMAD_GENOMES_ANNOTATION_KEY: {
                'AC_TEST': [13],
                'AN_TEST': 2,
                'AC_ZERO': [0],
                'AN_ZERO': 0
            }
        }

        converted = annotationconverters.gnomad_genomes_frequencies(annotation_source)[GNOMAD_GENOMES_RESULT_KEY]
        assert 'TEST' in converted['freq']
        assert float(13)/2 == converted['freq']['TEST']
        assert 'ZERO' not in converted['freq']

    def test_exac_hom_count_inclusion(self):
        annotation_source = {
            'EXAC': {
                'Hom_TEST': [13],
            }
        }

        converted = annotationconverters.exac_frequencies(annotation_source)[EXAC_RESULT_KEY]
        assert 'TEST' in converted['hom']
        assert 13 == converted['hom']['TEST']

    def test_esp_hom_count_inclusion(self):

        data = {
            'CSQ': [
                {
                    'EA_MAF': {
                        'G': 0.122
                    },
                    'AA_MAF': {
                        'G': 0.123
                    },
                    'Allele': 'G'
                },
                {}
            ]

        }

        freqs = annotationconverters.csq_frequencies(data)
        assert 0.122 == freqs['esp6500']['freq']['EA']
        assert 0.123 == freqs['esp6500']['freq']['AA']


class TestTranscriptAnnotation():

    def test_exon_distance(self):

        def generate_data(hgvsc):
            return {
                'CSQ': [
                    {
                        'Feature_type': 'Transcript',
                        'HGVSc': hgvsc
                    }
                ]
            }

        assert annotationconverters.convert_csq(generate_data('NM_007294.3:c.4535-213G>T'))[0]['exon_distance'] == -213
        assert annotationconverters.convert_csq(generate_data('NM_007294.3:c.4535+213G>T'))[0]['exon_distance'] == 213
        assert annotationconverters.convert_csq(generate_data('ENST123123:c.4535+1insAAA'))[0]['exon_distance'] == 1
        assert annotationconverters.convert_csq(generate_data('ENST123123:c.4535-1dupTTT'))[0]['exon_distance'] == -1
        assert annotationconverters.convert_csq(generate_data('ENST123123:c.4535+0dupTTT'))[0]['exon_distance'] == 0
        assert annotationconverters.convert_csq(generate_data('ENST123123:n.4535+1insAAA'))[0]['exon_distance'] == 1
        assert annotationconverters.convert_csq(generate_data('ENST123123:n.4535-1dupTTT'))[0]['exon_distance'] == -1
        assert 'exon_distance' not in annotationconverters.convert_csq(generate_data('ENST123123:c.4535G>T'))[0]
        assert 'exon_distance' not in annotationconverters.convert_csq(generate_data('NM_007294.3:c.4535G>T'))[0]
        assert 'exon_distance' not in annotationconverters.convert_csq(generate_data('ENST123123:n.4535G>T'))[0]
        assert 'exon_distance' not in annotationconverters.convert_csq(generate_data('NM_007294.3:n.4535G>T'))[0]

        with pytest.raises(AssertionError):
            annotationconverters.convert_csq(generate_data('NM_007294.3:c.4535-0G>T'))

    def test_get_is_last_exon(self):
        def generate_data(additions):
            data = {
                'CSQ': [
                    {
                        'Feature_type': 'Transcript',
                    }
                ]
            }
            data['CSQ'][0].update(additions)
            return data

        assert annotationconverters.convert_csq(generate_data({'EXON': '20/20'}))[0]['in_last_exon'] == 'yes'
        assert annotationconverters.convert_csq(generate_data({'EXON': '1/20'}))[0]['in_last_exon'] == 'no'
        assert annotationconverters.convert_csq(generate_data({}))[0]['in_last_exon'] == 'no'
        assert annotationconverters.convert_csq(generate_data({}))[0]['in_last_exon'] == 'no'
        with pytest.raises(IndexError):
            annotationconverters.convert_csq(generate_data({'EXON': '20__20'}))

    def test_csq_transcripts(self):
        data = {
            'CSQ': [
                {
                    'Feature': 'NM_000090.3',
                    'Feature_type': 'Transcript'
                },
                {
                    'Feature': 'ENS123456',
                    'Feature_type': 'Transcript'
                },
                {
                    'Feature': 'NM_000091.2',
                    'Feature_type': 'Transcript'
                },
                {
                    'Feature': 'NotTranscript',
                    'Feature_type': 'Other'
                }
            ]
        }

        transcripts = annotationconverters.convert_csq(data)

        assert len(transcripts) == 3
        assert transcripts[0]['transcript'] == 'NM_000090.3'
        assert transcripts[1]['transcript'] == 'ENS123456'
        assert transcripts[2]['transcript'] == 'NM_000091.2'