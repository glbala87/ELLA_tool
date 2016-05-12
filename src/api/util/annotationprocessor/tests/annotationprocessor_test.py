# coding=utf-8
import unittest

from ..annotationprocessor import FrequencyAnnotation, References, TranscriptAnnotation
from ..annotationprocessor import GenepanelCutoffsAnnotationProcessor
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
                'pubmedID': 1,
                'sources': ['VEP']
            }
        )
        self.assertEqual(
            pubmeds[1],
            {
                'pubmedID': 2,
                'sources': ['VEP']
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
                'pubmedID': 1,
                'sources': ['HGMD']
            }
        )
        self.assertEqual(
            pubmeds[1],
            {
                'pubmedID': 2,
                'sources': ['HGMD']
            }
        )
        self.assertEqual(
            pubmeds[2],
            {
                'pubmedID': 3,
                'sources': ['HGMD']
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
                'pubmedID': 1,
                'sources': ['VEP', 'HGMD']
            }
        )
        self.assertEqual(
            pubmeds[1],
            {
                'pubmedID': 2,
                'sources': ['VEP', 'HGMD']
            }
        )
        self.assertEqual(
            pubmeds[2],
            {
                'pubmedID': 3,
                'sources': ['HGMD']
            }
        )


class TestFrequencyAnnotation(unittest.TestCase):

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
        freq = FrequencyAnnotation(config.config).process(data)[FrequencyAnnotation.CONTRIBUTION_KEY]
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
        freq = FrequencyAnnotation(config.config).process(data)[FrequencyAnnotation.CONTRIBUTION_KEY]
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

        freqs = FrequencyAnnotation(config.config).process(data)[FrequencyAnnotation.CONTRIBUTION_KEY]
        self.assertIn('TEST', freqs['ExAC'])
        self.assertEqual(float(13)/2, freqs['ExAC']['TEST'])
        self.assertNotIn('ZERO', freqs['ExAC'])

    def test_exac_hom_count_inclusion(self):

        data = {
            'EXAC': {
                'Hom_TEST': [13],
            }
        }

        freqs = FrequencyAnnotation(config.config).process(data)[FrequencyAnnotation.CONTRIBUTION_KEY]
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

        freqs = FrequencyAnnotation(config.config).process(data)[FrequencyAnnotation.CONTRIBUTION_KEY]
        self.assertEqual(0.122, freqs['esp6500']['EA'])
        self.assertEqual(0.123, freqs['esp6500']['AA'])

    def test_frequency_cutoffs_from_none(self):

        processor = GenepanelCutoffsAnnotationProcessor(config.config, genepanel=None)
        frequencies = processor.cutoff_frequencies(None)

        self.assertEquals(frequencies["ExAC_cutoff"], "null_freq")
        self.assertEquals(frequencies["1000G_cutoff"], "null_freq")
        self.assertEquals(frequencies["ESP6500_cutoff"], "null_freq")
        self.assertEquals(frequencies["inDB_cutoff"], "null_freq")

    def test_frequency_cutoffs_from_empty(self):

        processor = GenepanelCutoffsAnnotationProcessor(config.config, genepanel=None)
        frequencies = processor.cutoff_frequencies({})

        self.assertEquals(frequencies["ExAC_cutoff"], "null_freq")
        self.assertEquals(frequencies["1000G_cutoff"], "null_freq")
        self.assertEquals(frequencies["ESP6500_cutoff"], "null_freq")
        self.assertEquals(frequencies["inDB_cutoff"], "null_freq")

    def test_frequency_cutoffs_1(self):

        annotation = {
            "1000g":
            {
                "ASN": 0.0005,
                "AMR": 0.000000001,
                "NOT_VALID": 1.0
            },
            "ExAC":
            {
                "AFR": 0.924688995215311,
            },
            "esp6500":
            {
                "AA": 0.00002,
                "EA": 0.0003
            }
        }
        processor = GenepanelCutoffsAnnotationProcessor(config.config, genepanel=None)
        frequencies = processor.cutoff_frequencies(annotation)

        self.assertEquals(frequencies["ExAC_cutoff"], "≥hi_freq_cutoff")
        self.assertEquals(frequencies["1000G_cutoff"], "<lo_freq_cutoff")
        self.assertEquals(frequencies["ESP6500_cutoff"], "<lo_freq_cutoff")
        self.assertEquals(frequencies["inDB_cutoff"], "null_freq")

    def test_frequency_cutoffs_2(self):

        annotation = {
            "1000g":
            {
                "ASN": 0.001, # Lower edge case
                "AMR": 0.000000001,
                "NOT_VALID": 1.0
            },
            "ExAC":
            {
                "AFR": 0.005,
            },
            "esp6500":
            {
                "AA": 0.00002,
                "EA": 0.0003
            }
        }
        processor = GenepanelCutoffsAnnotationProcessor(config.config, None)
        frequencies = processor.cutoff_frequencies(annotation)

        self.assertEquals(frequencies["ExAC_cutoff"], ["≥lo_freq_cutoff", "<hi_freq_cutoff"])
        self.assertEquals(frequencies["1000G_cutoff"], ["≥lo_freq_cutoff", "<hi_freq_cutoff"])
        self.assertEquals(frequencies["ESP6500_cutoff"], "<lo_freq_cutoff")
        self.assertEquals(frequencies["inDB_cutoff"], "null_freq")

    def test_frequency_cutoffs_3(self):
        annotation = {
            "1000g":
            {
                "ASN": 0.000001,
                "AMR": 0.00002,
                "NOT_VALID": 1.0
            },
            "ExAC":
            {
                "AFR": 0.000002,
            },
            "esp6500":
            {
                    "AA": 0.00002,
            },
             "inDB":
             {
                    "alleleFreq": 0.0022323
            }
        }
        processor = GenepanelCutoffsAnnotationProcessor(config.config, None)
        frequencies = processor.cutoff_frequencies(annotation)

        self.assertEquals(frequencies["ExAC_cutoff"], "<lo_freq_cutoff")
        self.assertEquals(frequencies["1000G_cutoff"], "<lo_freq_cutoff")
        self.assertEquals(frequencies["ESP6500_cutoff"], "<lo_freq_cutoff")
        self.assertEquals(frequencies["inDB_cutoff"], ["≥lo_freq_cutoff", "<hi_freq_cutoff"])


class TestTranscriptAnnotation(unittest.TestCase):

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
        genepanel = Genepanel(transcripts=[Transcript(refseqName='NM_000059.3', ensemblID='ENST00000544455'),
                                           Transcript(refseqName='NM_007294.3', ensemblID='ENST00000357654')],
                              version='v00',
                              name='HBOC')

        transcripts = ['NM_000059', 'NM_000058']

        t = TranscriptAnnotation.get_genepanel_transcripts(transcripts, genepanel)
        assert t == ['NM_000059']

    def test_get_genepanel_transcripts_versioned(self):
        genepanel = Genepanel(transcripts=[Transcript(refseqName='NM_000059.3', ensemblID='ENST00000544455'),
                                    Transcript(refseqName='NM_007294.3', ensemblID='ENST00000357654')],
                       version='v00',
                       name='HBOC')

        transcripts = ['NM_000059.3', 'NM_000058.1']

        t = TranscriptAnnotation.get_genepanel_transcripts(transcripts, genepanel)
        assert t == ['NM_000059']

    def test_get_genepanel_transcripts_multiple(self):

        gp = Genepanel(transcripts=[Transcript(refseqName='NM_000059.3', ensemblID='ENST00000544455'),
                                    Transcript(refseqName='NM_007294.3', ensemblID='ENST00000357654')],
                       version='v00',
                       name='HBOC')

        transcripts = ['NM_000059', 'NM_007294']

        t = TranscriptAnnotation.get_genepanel_transcripts(transcripts, gp)
        assert t == ['NM_000059', 'NM_007294']

    def test_get_genepanel_transcripts_none(self):
        genepanel = Genepanel(transcripts=[Transcript(refseqName='NM_000059.3', ensemblID='ENST00000544455')],
                       version='v00',
                       name='HBOC')

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
