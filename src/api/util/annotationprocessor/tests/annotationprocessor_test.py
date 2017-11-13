# coding=utf-8
import unittest

from ..annotationprocessor import TranscriptAnnotation, AnnotationProcessor

from vardb.datamodel.gene import Transcript, Genepanel


class TestTranscriptAnnotation(unittest.TestCase):

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
