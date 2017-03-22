# coding=utf-8
import unittest
import pytest

from ..annotationprocessor import TranscriptAnnotation, AnnotationProcessor, GenepanelCutoffsAnnotationProcessor, find_symbols

from vardb.datamodel.gene import Transcript, Genepanel


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
                        "inDB": ['AF']
                    }
                }
            }
        }
    }

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
                "freq": {
                    "G": 0.0005,
                    "NOT_VALID": 1.0
                }
            },
            "ExAC": {
                "freq": {
                    "G": 0.924688995215311,
                }
            },
            "esp6500": {
                "freq": {
                    "AA": 0.00002,
                    "EA": 0.0003
                }
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

    def test_frequency_cutoffs_2(self):

        annotation = {
            "1000g": {
                "freq": {
                    "G": 0.001,  # Lower edge case
                    "NOT_INCLUDED_IN_CONFIG": 1.0
                }
            },
            "ExAC": {
                "freq": {
                    "G": 0.005,
                }
            },
            "esp6500": {
                "freq": {
                    "AA": 0.00002,
                    "EA": 0.0003
                }
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
                "freq": {
                    "G": 0.1,
                    "NOT_IN_CONFIG": 1.0
                }
            },
            "ExAC": {
                "freq": {
                    "G": 0.000002,
                }
            },
            "esp6500": {
                "freq": {
                    "AA": 0.00005,
                    "EA": 0.99,
                }
            },
            "inDB": {
                "freq": {
                    "AF": 0.0022323
                }
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
        self.assertEquals(frequencies['cutoff']['internal']['inDB'], [">=lo_freq_cutoff", "<hi_freq_cutoff"])

    def test_frequency_cutoffs_4(self):

        annotation = {
            "1000g": {
                "freq": {
                    "G": 0.000001,
                    "NOT_IN_CONFIG": 1.0
                }
            },
            "ExAC": {
                "freq": {
                    "G": 0.000002,
                }
            },
            "esp6500": {
                "freq": {
                    "AA": 0.00002,
                    "EA": 0.00002,
                }
            },
            "inDB": {
                "freq": {
                    "AF": 0.0022323
                }
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
        self.assertEquals(frequencies['cutoff']['internal']['inDB'], [">=lo_freq_cutoff", "<hi_freq_cutoff"])


    def test_frequency_cutoffs_5(self):

        # Test multiple genes in config
        annotation = {
            "1000g": {
                "freq": {
                    "G": 0.000001,
                    "NOT_IN_CONFIG": 1.0
                }
            },
            "ExAC": {
                "freq": {
                    "G": 0.000002,
                }
            },
            "esp6500": {
                "freq": {
                    "AA": 0.2,
                    "EA": 0.2,
                }
            },
            "inDB": {
                "freq": {
                    "AF": 0.6
                }
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

        mock_gp = lambda: None
        mock_gp.find_inheritance = lambda x: None
        mock_gp.config = {
            'data': {
                'BRCA1': {
                    'freq_cutoffs': {
                        'external': {
                            'hi_freq_cutoff': 0.1,
                            'lo_freq_cutoff': 0.001
                        },
                        'internal': {
                            'hi_freq_cutoff': 0.1,
                            'lo_freq_cutoff': 0.01
                        }
                    },
                },
                'BRCA2': {
                    'freq_cutoffs': {
                        'external': {
                            'hi_freq_cutoff': 0.5,
                            'lo_freq_cutoff': 0.3
                        },
                        'internal': {
                            'hi_freq_cutoff': 0.9,
                            'lo_freq_cutoff': 0.7
                        }
                    }
                }
            }
        }

        processor = GenepanelCutoffsAnnotationProcessor(
            TestFrequencyAnnotation.MOCK_CONFIG,
            genepanel=mock_gp,
            genepanel_default=defaults
        )
        frequencies = processor.cutoff_frequencies(annotation, symbols=['BRCA1'])

        self.assertEquals(frequencies['cutoff']['external']['ExAC'], "<lo_freq_cutoff")
        self.assertEquals(frequencies['cutoff']['external']['1000g'], "<lo_freq_cutoff")
        self.assertEquals(frequencies['cutoff']['external']['esp6500'], ">=hi_freq_cutoff")
        self.assertEquals(frequencies['cutoff']['internal']['inDB'], ">=hi_freq_cutoff")

        frequencies = processor.cutoff_frequencies(annotation, symbols=['BRCA2'])

        self.assertEquals(frequencies['cutoff']['external']['ExAC'], "<lo_freq_cutoff")
        self.assertEquals(frequencies['cutoff']['external']['1000g'], "<lo_freq_cutoff")
        self.assertEquals(frequencies['cutoff']['external']['esp6500'], "<lo_freq_cutoff")
        self.assertEquals(frequencies['cutoff']['internal']['inDB'], "<lo_freq_cutoff")

        frequencies = processor.cutoff_frequencies(annotation, symbols=['BRCA2', 'BRCA1'])

        self.assertEquals(frequencies['cutoff']['external']['ExAC'], "<lo_freq_cutoff")
        self.assertEquals(frequencies['cutoff']['external']['1000g'], "<lo_freq_cutoff")
        self.assertEquals(frequencies['cutoff']['external']['esp6500'], ">=hi_freq_cutoff")
        self.assertEquals(frequencies['cutoff']['internal']['inDB'], ">=hi_freq_cutoff")


class TestTranscriptAnnotation(unittest.TestCase):

    def test_get_genepanel_transcripts_normal(self):
        genepanel = Genepanel(transcripts=[Transcript(refseq_name='NM_000059.3', ensembl_id='ENST00000544455'),
                                           Transcript(refseq_name='NM_007294.3', ensembl_id='ENST00000357654')],
                              version='v01',
                              name='HBOCUTV')

        transcripts = ['NM_000059.3', 'NM_000058.2']

        t = TranscriptAnnotation.get_genepanel_transcripts(transcripts, genepanel)
        assert t == ['NM_000059.3']

    def test_get_genepanel_transcripts_versioned(self):
        genepanel = Genepanel(transcripts=[Transcript(refseq_name='NM_000059.3', ensembl_id='ENST00000544455'),
                                           Transcript(refseq_name='NM_007294.3', ensembl_id='ENST00000357654')],
                              version='v01',
                              name='HBOCUTV')

        transcripts = ['NM_000059.3', 'NM_000058.1']

        t = TranscriptAnnotation.get_genepanel_transcripts(transcripts, genepanel)
        assert t == ['NM_000059.3']

    def test_get_genepanel_transcripts_multiple(self):

        gp = Genepanel(transcripts=[Transcript(refseq_name='NM_000059.3', ensembl_id='ENST00000544455'),
                                    Transcript(refseq_name='NM_007294.3', ensembl_id='ENST00000357654')],
                       version='v01',
                       name='HBOCUTV')

        transcripts = ['NM_000059.3', 'NM_007294.3']

        t = TranscriptAnnotation.get_genepanel_transcripts(transcripts, gp)
        assert t == ['NM_000059.3', 'NM_007294.3']

    def test_get_genepanel_transcripts_none(self):
        genepanel = Genepanel(transcripts=[Transcript(refseq_name='NM_000059.3', ensembl_id='ENST00000544455')],
                              version='v01',
                              name='HBOCUTV')

        transcripts = ['NM_000051.3']

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
                'transcript': 'NM_12300.3',
                'consequences': ['consequence3', 'consequence2']
            },
            {
                'transcript': 'NM_12301.2',
                'consequences': ['consequence1']
            },
            {
                'transcript': 'NM_12302.3',
                'consequences': ['consequence3', 'consequence1']
            }
        ]

        # Test several worst consequences
        c = TranscriptAnnotation(config)._get_worst_consequence(transcripts)
        assert c == ['NM_12301.2', 'NM_12302.3']

        transcripts = [
            {
                'transcript': 'NM_12300.3',
                'consequences': ['consequence1']
            },
            {
                'transcript': 'NM_12301.2',
                'consequences': ['consequence2']
            }
        ]

        # Test single worst
        c = TranscriptAnnotation(config)._get_worst_consequence(transcripts)
        assert c == ['NM_12300.3']

    def test_custom_annotation_references(self):

        # Test merging references from internal and custom annotation

        annotation = {
            'references': [
                {
                    'pubmed_id': 1234,
                    'sources': ['VEP']
                },
                {
                    'pubmed_id': 4321
                },
            ]
        }
        custom_annotation = {
            'references': [
                {
                    'pubmed_id': 9874,
                    'sources': ['User']
                },
                {
                    'id': 845,
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
      'transcripts': [{'symbol': 'Gene X'}, {'symbol': 'Gene X'}]
     }, ['Gene X']),

    ({
      'filtered_transcripts': ['NM_2'],
      'transcripts': [{'transcript': 'NM_1', 'symbol': 'Gene X'}, {'transcript': 'NM_2', 'symbol': 'Gene Y'}]
     }, ['Gene Y']),
    ({
      'filtered_transcripts': [],
      'transcripts': [{'transcript': 'NM_1', 'symbol': 'Gene X'}, {'transcript': 'NM_2', 'symbol': 'Gene Y'}]
     }, ['Gene X', 'Gene Y'])
])
def test_find_symbol_from_transcripts(annotation, symbol):
    assert find_symbols(annotation) == symbol
