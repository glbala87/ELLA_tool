# coding=utf-8
import unittest
from ..annotationprocessor import FrequencyAnnotation, References, TranscriptAnnotation

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

        pubmeds = References().process(data)['references']
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

        pubmeds = References().process(data)['references']
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

        pubmeds = References().process(data)['references']
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
        freq = FrequencyAnnotation().process(data)['frequencies']
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
        freq = FrequencyAnnotation().process(data)['frequencies']
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

        freqs = FrequencyAnnotation().process(data)['frequencies']
        self.assertIn('TEST', freqs['ExAC'])
        self.assertEqual(float(13)/2, freqs['ExAC']['TEST'])
        self.assertNotIn('ZERO', freqs['ExAC'])

    def test_exac_hom_count_inclusion(self):

        data = {
            'EXAC': {
                'Hom_TEST': [13],
            }
        }

        freqs = FrequencyAnnotation().process(data)['frequencies']
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

        freqs = FrequencyAnnotation().process(data)['frequencies']
        self.assertEqual(0.122, freqs['esp6500']['EA'])
        self.assertEqual(0.123, freqs['esp6500']['AA'])

    def test_frequency_cutoffs(self):
        frequencies = FrequencyAnnotation()._cutoff_frequencies(None)
        self.assertEquals(frequencies["ExAC_1000G_ESP6500_cutoff"], "null_freq")
        self.assertEquals(frequencies["inDB_cutoff"], "null_freq")

        frequencies = FrequencyAnnotation()._cutoff_frequencies({})
        self.assertEquals(frequencies["ExAC_1000G_ESP6500_cutoff"], "null_freq")
        self.assertEquals(frequencies["inDB_cutoff"], "null_freq")

        frequencies = {
            "1000g":
            {
                "AFR": 0.0005,
                "AMR": 0.000000001,
                "FOO": 0.004
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
        frequencies = FrequencyAnnotation()._cutoff_frequencies(frequencies)
        self.assertEquals(frequencies["ExAC_1000G_ESP6500_cutoff"], "≥hi_freq_cutoff")
        self.assertEquals(frequencies["inDB_cutoff"], "null_freq")

        frequencies = {
            "1000g":
            {
                "AFR": 0.0005,
                "AMR": 0.000000001,
                "FOO": 0.004
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
        frequencies = FrequencyAnnotation()._cutoff_frequencies(frequencies)
        self.assertEquals(frequencies["ExAC_1000G_ESP6500_cutoff"], ["≥lo_freq_cutoff", "<hi_freq_cutoff"])
        self.assertEquals(frequencies["inDB_cutoff"], "null_freq")

        frequencies = {
            "1000g":
            {
                "AFR": 0.000001,
                "AMR": 0.00002,
                "FOO": 0.000002
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
        frequencies = FrequencyAnnotation()._cutoff_frequencies(frequencies)
        self.assertEquals(frequencies["ExAC_1000G_ESP6500_cutoff"], "<lo_freq_cutoff")
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

        transcripts = TranscriptAnnotation()._csq_transcripts(data)

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

        transcripts = TranscriptAnnotation().process(data)
        self.assertEqual(transcripts['transcripts'][0]['Transcript'], 'NM_000090')
        self.assertEqual(transcripts['transcripts'][0]['Transcript_version'], '3')
        self.assertEqual(transcripts['transcripts'][1]['Transcript'], 'NM_000091')
        self.assertEqual(transcripts['transcripts'][1]['Transcript_version'], '2')
        self.assertEqual(transcripts['transcripts'][1][TranscriptAnnotation.CSQ_FIELDS[0]], 'TEST2')

    def test_get_genepanel_transcripts_normal(self):

        genepanel = {
            'transcripts': [
                {
                    'ensemblID': 'ENST00000544455',
                    'refseqName': 'NM_000059.3'
                },
                {
                    'ensemblID': 'ENST00000357654',
                    'refseqName': 'NM_007294.3'
                }
            ],
            'version': 'v00',
            'name': 'HBOC'
        }

        transcripts = ['NM_000059', 'NM_000058']

        t = TranscriptAnnotation.get_genepanel_transcripts(transcripts, genepanel)
        assert t == ['NM_000059']

    def test_get_genepanel_transcripts_versioned(self):

        genepanel = {
            'transcripts': [
                {
                    'ensemblID': 'ENST00000544455',
                    'refseqName': 'NM_000059.3'
                },
                {
                    'ensemblID': 'ENST00000357654',
                    'refseqName': 'NM_007294.3'
                }
            ],
            'version': 'v00',
            'name': 'HBOC'
        }

        transcripts = ['NM_000059.3', 'NM_000058.1']

        t = TranscriptAnnotation.get_genepanel_transcripts(transcripts, genepanel)
        assert t == ['NM_000059']

    def test_get_genepanel_transcripts_multiple(self):

        genepanel = {
            'transcripts': [
                {
                    'ensemblID': 'ENST00000544455',
                    'refseqName': 'NM_000059.3'
                },
                {
                    'ensemblID': 'ENST00000357654',
                    'refseqName': 'NM_007294.3'
                }
            ],
            'version': 'v00',
            'name': 'HBOC'
        }

        transcripts = ['NM_000059', 'NM_007294']

        t = TranscriptAnnotation.get_genepanel_transcripts(transcripts, genepanel)
        assert t == ['NM_000059', 'NM_007294']

    def test_get_genepanel_transcripts_none(self):

        genepanel = {
            'transcripts': [
                {
                    'ensemblID': 'ENST00000544455',
                    'refseqName': 'NM_000059.3'
                },
                {
                    'ensemblID': 'ENST00000357654',
                    'refseqName': 'NM_007294.3'
                }
            ],
            'version': 'v00',
            'name': 'HBOC'
        }

        transcripts = ['NM_000051']

        t = TranscriptAnnotation.get_genepanel_transcripts(transcripts, genepanel)
        assert t == []
