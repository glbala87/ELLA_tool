# coding=utf-8
import unittest

from ..annotationprocessor import TranscriptAnnotation, AnnotationProcessor

from vardb.datamodel.gene import Transcript, Genepanel


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
