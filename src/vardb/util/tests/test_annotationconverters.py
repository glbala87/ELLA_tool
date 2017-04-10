# coding=utf-8
import unittest
import pytest

from .. import annotationconverters

class TestReferences():

    def test_get_pubmeds_CSQ(self):
        data = {
            'CSQ': [
                {
                    'PUBMED': [
                        1,
                        2
                    ]
                },
                {}
            ]

        }

        pubmeds = annotationconverters.ConvertReferences().process(data)
        assert pubmeds[0] == {
                'pubmed_id': 1,
                'sources': ['VEP'],
                'source_info': {},
            }

        assert pubmeds[1] == {
                'pubmed_id': 2,
                'sources': ['VEP'],
                'source_info': {},
            }

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

    def test_get_pubmeds_both(self):
        data = {
            'CSQ': [
                {
                    'PUBMED': [
                        1,
                        2
                    ]
                }
            ],
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
                'sources': ['VEP', 'HGMD'],
                'source_info': {"HGMD": "Primary literature report. No comments."},
            }

        assert pubmeds[1] == {
                'pubmed_id': 2,
                'sources': ['VEP', 'HGMD'],
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

        data = {
            'EXAC': {
                'AC_TEST': [13],
                'AN_TEST': 2,
                'AC_ZERO': [0],
                'AN_ZERO': 0
            }
        }

        freqs = annotationconverters.exac_frequencies(data)
        assert 'TEST' in freqs['ExAC']['freq']
        assert float(13)/2 == freqs['ExAC']['freq']['TEST']
        assert 'ZERO' not in freqs['ExAC']['freq']

    def test_exac_hom_count_inclusion(self):

        data = {
            'EXAC': {
                'Hom_TEST': [13],
            }
        }

        freqs = annotationconverters.exac_frequencies(data)
        assert 'TEST' in freqs['ExAC']['hom']
        assert 13 == freqs['ExAC']['hom']['TEST']

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
        assert 'exon_distance' not in annotationconverters.convert_csq(generate_data('ENST123123:c.4535G>T'))[0]
        assert 'exon_distance' not in annotationconverters.convert_csq(generate_data('NM_007294.3:c.4535G>T'))[0]

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
