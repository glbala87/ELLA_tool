# coding=utf-8
import unittest
import pytest

from ..annotationprocessor import FrequencyAnnotation, References, TranscriptAnnotation
from ..annotationprocessor import TranscriptAnnotation, AnnotationProcessor
from ..annotationprocessor import GenepanelCutoffsAnnotationProcessor, find_symbol
from api import config
from vardb.datamodel.gene import Transcript, Genepanel


class TestReferences(unittest.TestCase):

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

        pubmeds = References().process(data)[References.CONTRIBUTION_KEY]
        self.assertEqual(
            pubmeds[0],
            {
                'pubmed_id': 1,
                'sources': ['VEP'],
                'sourceInfo': {},
            }
        )
        self.assertEqual(
            pubmeds[1],
            {
                'pubmed_id': 2,
                'sources': ['VEP'],
                'sourceInfo': {},
            }
        )

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

        pubmeds = References().process(data)[References.CONTRIBUTION_KEY]
        self.assertEqual(
            pubmeds[0],
            {
                'pubmed_id': 1,
                'sources': ['HGMD'],
                'sourceInfo': {"HGMD": "Primary literature report. No comments."},
            }
        )
        self.assertEqual(
            pubmeds[1],
            {
                'pubmed_id': 2,
                'sources': ['HGMD'],
                'sourceInfo': {'HGMD': "Reftag not specified. No comments."},
            }
        )
        self.assertEqual(
            pubmeds[2],
            {
                'pubmed_id': 3,
                'sources': ['HGMD'],
                'sourceInfo': {'HGMD': "Reftag not specified. No comments."},
            }
        )

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

        pubmeds = References().process(data)[References.CONTRIBUTION_KEY]
        self.assertEqual(
            pubmeds[0],
            {
                'pubmed_id': 1,
                'sources': ['VEP', 'HGMD'],
                'sourceInfo': {"HGMD": "Primary literature report. No comments."},
            }
        )
        self.assertEqual(
            pubmeds[1],
            {
                'pubmed_id': 2,
                'sources': ['VEP', 'HGMD'],
                'sourceInfo': {'HGMD': "Reftag not specified. No comments."},
            }
        )
        self.assertEqual(
            pubmeds[2],
            {
                'pubmed_id': 3,
                'sources': ['HGMD'],
                'sourceInfo': {'HGMD': "Reftag not specified. No comments."},
            }
        )


class TestFrequencyAnnotation(unittest.TestCase):

    MOCK_CONFIG = {
        "variant_criteria": {
            "frequencies": {  # Frequency groups to be used as part of cutoff calculation (and by extension class 1 filtering)
                "groups": {
                    "external": {
                        "ExAC": ["G"],
                        "1000g": ["G"],
                        "esp6500": ["AA", "EA"]
                    },
                    "internal": {
                        "inDB": ['alleleFreq']
                    }
                }
            }
        }
    }

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
        freq = FrequencyAnnotation(TestFrequencyAnnotation.MOCK_CONFIG).process(data)[FrequencyAnnotation.CONTRIBUTION_KEY]
        self.assertFalse('GMAF' in freq['1000g'])

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
        freq = FrequencyAnnotation(TestFrequencyAnnotation.MOCK_CONFIG).process(data)[FrequencyAnnotation.CONTRIBUTION_KEY]
        self.assertIn('G', freq['1000g'])
        self.assertNotIn('GMAF', freq['1000g'])
        self.assertIn('EUR', freq['1000g'])
        self.assertNotIn('EUR_MAF', freq['1000g'])

    def test_exac_conversion(self):

        data = {
            'EXAC': {
                'AC_TEST': [13],
                'AN_TEST': 2,
                'AC_ZERO': [0],
                'AN_ZERO': 0
            }
        }

        freqs = FrequencyAnnotation(TestFrequencyAnnotation.MOCK_CONFIG).process(data)[FrequencyAnnotation.CONTRIBUTION_KEY]
        self.assertIn('TEST', freqs['ExAC'])
        self.assertEqual(float(13)/2, freqs['ExAC']['TEST'])
        self.assertNotIn('ZERO', freqs['ExAC'])

    def test_exac_hom_count_inclusion(self):

        data = {
            'EXAC': {
                'Hom_TEST': [13],
            }
        }

        freqs = FrequencyAnnotation(TestFrequencyAnnotation.MOCK_CONFIG).process(data)[FrequencyAnnotation.CONTRIBUTION_KEY]
        self.assertIn('TEST', freqs['ExAC']['hom'])
        self.assertEqual(13, freqs['ExAC']['hom']['TEST'])

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

        freqs = FrequencyAnnotation(TestFrequencyAnnotation.MOCK_CONFIG).process(data)[FrequencyAnnotation.CONTRIBUTION_KEY]
        self.assertEqual(0.122, freqs['esp6500']['EA'])
        self.assertEqual(0.123, freqs['esp6500']['AA'])

    def test_frequency_cutoffs_from_none(self):

        processor = GenepanelCutoffsAnnotationProcessor(TestFrequencyAnnotation.MOCK_CONFIG, genepanel=None)
        frequencies = processor.cutoff_frequencies(None)

        self.assertEquals(frequencies['cutoff']['external']["ExAC"], "null_freq")
        self.assertEquals(frequencies['cutoff']['external']["1000g"], "null_freq")
        self.assertEquals(frequencies['cutoff']['external']["esp6500"], "null_freq")
        self.assertEquals(frequencies['cutoff']['internal']["inDB"], "null_freq")

    def test_frequency_cutoffs_from_empty(self):

        processor = GenepanelCutoffsAnnotationProcessor(TestFrequencyAnnotation.MOCK_CONFIG, genepanel=None)
        frequencies = processor.cutoff_frequencies({})

        self.assertEquals(frequencies['cutoff']['external']["ExAC"], "null_freq")
        self.assertEquals(frequencies['cutoff']['external']["1000g"], "null_freq")
        self.assertEquals(frequencies['cutoff']['external']["esp6500"], "null_freq")
        self.assertEquals(frequencies['cutoff']['internal']["inDB"], "null_freq")

    def test_frequency_cutoffs_1(self):

        annotation = {
            "1000g": {
                "G": 0.0005,
                "NOT_VALID": 1.0
            },
            "ExAC": {
                "G": 0.924688995215311,
            },
            "esp6500": {
                "AA": 0.00002,
                "EA": 0.0003
            }
        }

        processor = GenepanelCutoffsAnnotationProcessor(
            TestFrequencyAnnotation.MOCK_CONFIG,
            genepanel=None
        )
        frequencies = processor.cutoff_frequencies(annotation)

        self.assertEquals(frequencies['cutoff']['external']['1000g'], "<lo_freq_cutoff")
        self.assertEquals(frequencies['cutoff']['external']['esp6500'], "<lo_freq_cutoff")
        self.assertEquals(frequencies['cutoff']['internal']['inDB'], "null_freq")
        self.assertEquals(frequencies['cutoff']['external']['ExAC'], ">=hi_freq_cutoff")


def test_frequency_cutoffs_2():

    annotation = {
        "1000g": {
            "G": 0.001,  # Lower edge case
            "NOT_INCLUDED_IN_CONFIG": 1.0
        },
        "ExAC": {
            "G": 0.005,
        },
        "esp6500": {
            "AA": 0.00002,
            "EA": 0.0003
        }
    }

    defaults = {
        'freq_cutoffs': {
            'default': {
                'external': {
                    'hi_freq_cutoff': 0.01,
                    'lo_freq_cutoff': 0.001
                },
                'internal': {
                    'hi_freq_cutoff': 0.01,
                    'lo_freq_cutoff': 0.001
                }
            }
        }
    }
    processor = GenepanelCutoffsAnnotationProcessor(
        TestFrequencyAnnotation.MOCK_CONFIG,
        genepanel=None,
        genepanel_default=defaults
    )

    frequencies = processor.cutoff_frequencies(annotation)

    assert frequencies['cutoff']['external']["ExAC"] == [">=lo_freq_cutoff", "<hi_freq_cutoff"]
    assert frequencies['cutoff']['external']["1000g"] == [">=lo_freq_cutoff", "<hi_freq_cutoff"]
    assert frequencies['cutoff']['external']["esp6500"] == "<lo_freq_cutoff"
    assert frequencies['cutoff']['internal']["inDB"] == "null_freq"

    def test_frequency_cutoffs_3(self):
        # Test that when there's multiple items in a group (AA, EA),
        # the highest cutoff is returned (i.e >=hi_freq_cutoff instead of <lo_freq_cutoff).

        annotation = {
            "1000g": {
                "G": 0.1,
                "NOT_IN_CONFIG": 1.0
            },
            "ExAC": {
                "G": 0.000002,
            },
            "esp6500": {
                    "AA": 0.00005,
                    "EA": 0.99,
            },
             "inDB": {
                    "alleleFreq": 0.0022323
            }
        }

        defaults = {
            'freq_cutoffs': {
                'default': {
                    'external': {
                        'hi_freq_cutoff': 0.01,
                        'lo_freq_cutoff': 0.001
                    },
                    'internal': {
                        'hi_freq_cutoff': 0.01,
                        'lo_freq_cutoff': 0.001
                    }
                }
            }
        }

        processor = GenepanelCutoffsAnnotationProcessor(
            TestFrequencyAnnotation.MOCK_CONFIG,
            genepanel=None,
            genepanel_default=defaults
        )
        frequencies = processor.cutoff_frequencies(annotation)

        self.assertEquals(frequencies['cutoff']['external']['esp6500'], ">=hi_freq_cutoff")
        self.assertEquals(frequencies['cutoff']['external']['ExAC'], "<lo_freq_cutoff")
        self.assertEquals(frequencies['cutoff']['external']['1000g'], ">=hi_freq_cutoff")
        self.assertEquals(frequencies['cutoff']['internal']['inDB'], "<lo_freq_cutoff")

    def test_frequency_cutoffs_4(self):

        annotation = {
            "1000g": {
                "G": 0.000001,
                "NOT_IN_CONFIG": 1.0
            },
            "ExAC": {
                "G": 0.000002,
            },
            "esp6500": {
                    "AA": 0.00002,
                    "EA": 0.00002,
            },
             "inDB": {
                    "alleleFreq": 0.0022323
            }
        }

        defaults = {
            'freq_cutoffs': {
                'default': {
                    'external': {
                        'hi_freq_cutoff': 0.01,
                        'lo_freq_cutoff': 0.001
                    },
                    'internal': {
                        'hi_freq_cutoff': 0.01,
                        'lo_freq_cutoff': 0.001
                    }
                }
            }
        }

        processor = GenepanelCutoffsAnnotationProcessor(
            TestFrequencyAnnotation.MOCK_CONFIG,
            genepanel=None,
            genepanel_default=defaults
        )
        frequencies = processor.cutoff_frequencies(annotation)

        self.assertEquals(frequencies['cutoff']['external']['ExAC'], "<lo_freq_cutoff")
        self.assertEquals(frequencies['cutoff']['external']['1000g'], "<lo_freq_cutoff")
        self.assertEquals(frequencies['cutoff']['external']['esp6500'], "<lo_freq_cutoff")
        self.assertEquals(frequencies['cutoff']['internal']['inDB'], "<lo_freq_cutoff")


class TestTranscriptAnnotation(unittest.TestCase):


    def test_get_transcript_intronic(self):

        config = {
            'variant_criteria': {
                "intronic_region": {
                    "-": 20,
                    "+": 6
                }
            }
        }

        ta = TranscriptAnnotation(config)

        # Normal positive
        assert ta._get_transcript_intronic({
            'Consequence': ['intron_variant'],
            'HGVSc': 'NM_007294.3:c.4535-213G>T'
        })

        # Non-intronic HGVSc, yet intronic Consequence
        assert not ta._get_transcript_intronic({
            'Consequence': ['intron_variant'],
            'HGVSc': 'NM_007294.3:c.4535G>T'
        })

        # Intronic HGVSc, non-intronic Consequence
        assert not ta._get_transcript_intronic({
            'Consequence': ['stop_gained'],
            'HGVSc': 'NM_007294.3:c.4535-213G>T'
        })

        # Non-intronic HGVSc, non-intronic Consequence
        assert not ta._get_transcript_intronic({
            'Consequence': ['stop_gained'],
            'HGVSc': 'NM_012463.3:c.1246G>A'
        })

        # Garbage HGVSc, intronic Consequence
        assert not ta._get_transcript_intronic({
            'Consequence': ['intron_variant'],
            'HGVSc': 'NM_007294.3:c.535AA+234G>T'
        })

        # HGVSc inside region
        assert not ta._get_transcript_intronic({
            'Consequence': ['intron_variant'],
            'HGVSc': 'NM_007294.3:c.535+5G>T'
        })

        # HGVSc inside region
        assert not ta._get_transcript_intronic({
            'Consequence': ['intron_variant'],
            'HGVSc': 'NM_007294.3:c.535-19G>T'
        })

        # HGVSc at region (region is not inclusive)
        assert not ta._get_transcript_intronic({
            'Consequence': ['intron_variant'],
            'HGVSc': 'NM_007294.3:c.535+6G>T'
        })

        # HGVSc at region (region is not inclusive)
        assert not ta._get_transcript_intronic({
            'Consequence': ['intron_variant'],
            'HGVSc': 'NM_007294.3:c.535-20G>T'
        })

        # HGVSc region +1
        assert ta._get_transcript_intronic({
            'Consequence': ['intron_variant'],
            'HGVSc': 'NM_007294.3:c.535+7G>T'
        })

        # HGVSc region +1
        assert ta._get_transcript_intronic({
            'Consequence': ['intron_variant'],
            'HGVSc': 'NM_007294.3:c.535-21G>T'
        })

        # No filtering when missing config
        assert not TranscriptAnnotation({})._get_transcript_intronic({
            'Consequence': ['intron_variant'],
            'HGVSc': 'NM_007294.3:c.535-200G>T'
        })

    def test_get_is_last_exon(self):

        # Test for last exon
        self.assertTrue(
            TranscriptAnnotation({})._get_is_last_exon({'EXON': '20/20'})
        )

        # Test for not last exon
        self.assertFalse(
            TranscriptAnnotation({})._get_is_last_exon({'EXON': '1/20'})
        )

        # Test for missing field
        self.assertFalse(
            TranscriptAnnotation({})._get_is_last_exon({})
        )

        # Test for broken data
        with self.assertRaises(IndexError):
            TranscriptAnnotation({})._get_is_last_exon({'EXON': '20___20'}),

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
                    'Feature_type': 'Transcript',
                    TranscriptAnnotation.CSQ_FIELDS[0]: 'TEST'
                },
                {
                    'Feature': 'NotTranscript',
                    'Feature_type': 'Other'
                }
            ]
        }

        transcripts = TranscriptAnnotation({})._csq_transcripts(data)

        self.assertIn('NM_000090', transcripts)
        self.assertIn('NM_000091', transcripts)
        self.assertEqual(
            transcripts['NM_000091'][TranscriptAnnotation.CSQ_FIELDS[0]],
            'TEST'
        )
        self.assertEqual(transcripts['NM_000090']['Transcript'], 'NM_000090')
        self.assertEqual(transcripts['NM_000090']['Transcript_version'], '3')

        self.assertEqual(transcripts['NM_000091']['Transcript'], 'NM_000091')
        self.assertEqual(transcripts['NM_000091']['Transcript_version'], '2')

        # Test stripping away non-NM transcripts
        self.assertNotIn('ENS123456', transcripts)

        self.assertNotIn('NotTranscript', transcripts)

    def test_all_transcripts(self):
        data = {
            'CSQ': [
                {
                    'Feature': 'NM_000090.3',
                    'Feature_type': 'Transcript',
                    TranscriptAnnotation.CSQ_FIELDS[0]: 'TEST'
                },
                {
                    'Feature': 'NM_000091.2',
                    'Feature_type': 'Transcript',
                    TranscriptAnnotation.CSQ_FIELDS[0]: 'TEST2'
                }
            ]
        }

        transcripts = TranscriptAnnotation({}).process(data)[TranscriptAnnotation.CONTRIBUTION_KEY]
        self.assertEqual(transcripts[0]['Transcript'], 'NM_000090')
        self.assertEqual(transcripts[0]['Transcript_version'], '3')
        self.assertEqual(transcripts[1]['Transcript'], 'NM_000091')
        self.assertEqual(transcripts[1]['Transcript_version'], '2')
        self.assertEqual(transcripts[1][TranscriptAnnotation.CSQ_FIELDS[0]], 'TEST2')

    def test_get_genepanel_transcripts_normal(self):
        genepanel = Genepanel(transcripts=[Transcript(refseq_name='NM_000059.3', ensembl_id='ENST00000544455'),
                                           Transcript(refseq_name='NM_007294.3', ensembl_id='ENST00000357654')],
                              version='v01',
                              name='HBOCUTV')

        transcripts = ['NM_000059', 'NM_000058']

        t = TranscriptAnnotation.get_genepanel_transcripts(transcripts, genepanel)
        assert t == ['NM_000059']

    def test_get_genepanel_transcripts_versioned(self):
        genepanel = Genepanel(transcripts=[Transcript(refseq_name='NM_000059.3', ensembl_id='ENST00000544455'),
                                    Transcript(refseq_name='NM_007294.3', ensembl_id='ENST00000357654')],
                       version='v01',
                       name='HBOCUTV')

        transcripts = ['NM_000059.3', 'NM_000058.1']

        t = TranscriptAnnotation.get_genepanel_transcripts(transcripts, genepanel)
        assert t == ['NM_000059']

    def test_get_genepanel_transcripts_multiple(self):

        gp = Genepanel(transcripts=[Transcript(refseq_name='NM_000059.3', ensembl_id='ENST00000544455'),
                                    Transcript(refseq_name='NM_007294.3', ensembl_id='ENST00000357654')],
                       version='v01',
                       name='HBOCUTV')

        transcripts = ['NM_000059', 'NM_007294']

        t = TranscriptAnnotation.get_genepanel_transcripts(transcripts, gp)
        assert t == ['NM_000059', 'NM_007294']

    def test_get_genepanel_transcripts_none(self):
        genepanel = Genepanel(transcripts=[Transcript(refseq_name='NM_000059.3', ensembl_id='ENST00000544455')],
                       version='v01',
                       name='HBOCUTV')

        transcripts = ['NM_000051']

        t = TranscriptAnnotation.get_genepanel_transcripts(transcripts, genepanel)
        assert t == []

    def test_get_worse_consequence(self):
        config = {
            'transcripts': {
                'consequences': [  # Gives order of severity
                    'consequence1',
                    'consequence2',
                    'consequence3'
                ]
            }
        }

        transcripts = [
            {
                'Transcript': 'NM_12300',
                'Consequence': ['consequence3', 'consequence2']
            },
            {
                'Transcript': 'NM_12301',
                'Consequence': ['consequence1']
            },
            {
                'Transcript': 'NM_12302',
                'Consequence': ['consequence3', 'consequence1']
            }
        ]

        # Test several worst consequences
        c = TranscriptAnnotation(config)._get_worst_consequence(transcripts)
        assert c == ['NM_12301', 'NM_12302']

        transcripts = [
            {
                'Transcript': 'NM_12300',
                'Consequence': ['consequence1']
            },
            {
                'Transcript': 'NM_12301',
                'Consequence': ['consequence2']
            }
        ]

        # Test single worst
        c = TranscriptAnnotation(config)._get_worst_consequence(transcripts)
        assert c == ['NM_12300']

    def test_custom_annotation_references(self):

        # Test merging references from internal and custom annotation

        annotation = {
            'CSQ': [
                {
                    'PUBMED': [1234, 2345]
                }
            ]
        }
        custom_annotation = {
            'references': [
                {
                    'pubmed_id': 9874,
                    'sources': ['User']
                },
                {
                    'some_other_id': 845,
                    'sources': ['Something']
                },
                {
                    'pubmed_id': 1234,  # Also in annotation
                    'sources': ['User']
                }
            ]
        }

        result = AnnotationProcessor.process(annotation, custom_annotation=custom_annotation)
        assert len(result['references']) == 4
        # Fetch the one in both annotations
        in_both_ref = [r for r in result['references'] if r.get('pubmed_id') == 1234]
        assert len(in_both_ref) == 1
        assert 'User' in in_both_ref[0]['sources']
        assert 'VEP' in in_both_ref[0]['sources']


@pytest.mark.parametrize("annotation, symbol", [
    ({
      TranscriptAnnotation.CONTRIBUTION_KEY: [{'SYMBOL': 'Gene X'}, {'SYMBOL': 'Gene X'}]
     }, 'Gene X'),

    ({
      TranscriptAnnotation.CONTRIBUTION_KEY_FILTERED_TRANSCRIPTS: ['NM_2'],
      TranscriptAnnotation.CONTRIBUTION_KEY: [{'Transcript': 'NM_1', 'SYMBOL': 'Gene X'}, {'Transcript': 'NM_2', 'SYMBOL': 'Gene Y'}]
     }, 'Gene Y')
])
def test_find_symbol_from_transcripts(annotation, symbol):
    assert find_symbol(annotation) == symbol


def test_find_symbol_raise_exception():
    with pytest.raises(Exception) as exc:
         find_symbol({
          TranscriptAnnotation.CONTRIBUTION_KEY: [{'SYMBOL': 'Gene X'}, {'SYMBOL': 'Gene Y'}],
          'annotation_id': 1
         })
    assert exc
    assert "Gene X" in exc.value.message
    assert "Gene Y" in exc.value.message
