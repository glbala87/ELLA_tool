# coding=utf-8
import unittest

from datalayer.alleledataloader.annotationprocessor import TranscriptAnnotation, AnnotationProcessor


class TestTranscriptAnnotation(unittest.TestCase):
    def test_get_worse_consequence(self):
        config = {
            "transcripts": {
                "consequences": ["consequence1", "consequence2", "consequence3"]
            }  # Gives order of severity
        }

        # Test several transcripts with worst consequence among multiple
        transcripts = [
            {"transcript": "NM_12300.3", "consequences": ["consequence3", "consequence2"]},
            {"transcript": "NM_12301.2", "consequences": ["consequence1"]},
            {"transcript": "NM_12302.3", "consequences": ["consequence3", "consequence1"]},
        ]

        c = TranscriptAnnotation(config)._get_worst_consequence(transcripts)
        assert c == ["NM_12301.2", "NM_12302.3"]

        # Test one transcript with worst consequence among multiple
        transcripts = [
            {"transcript": "NM_12300.3", "consequences": ["consequence3", "consequence2"]},
            {"transcript": "NM_12301.2", "consequences": ["consequence3"]},
            {"transcript": "NM_12302.3", "consequences": ["consequence3", "consequence1"]},
        ]

        c = TranscriptAnnotation(config)._get_worst_consequence(transcripts)
        assert c == ["NM_12302.3"]

        # Test one transcript with worst consequence, one missing
        transcripts = [
            {"transcript": "NM_12300.3", "consequences": ["consequence3", "consequence2"]},
            {"transcript": "NM_12301.2", "consequences": []},
            {"transcript": "NM_12302.3", "consequences": ["consequence3", "consequence1"]},
        ]

        c = TranscriptAnnotation(config)._get_worst_consequence(transcripts)
        assert c == ["NM_12302.3"]

        # Test single transcript with worst consequence
        transcripts = [
            {"transcript": "NM_12300.3", "consequences": ["consequence1"]},
            {"transcript": "NM_12301.2", "consequences": ["consequence2"]},
        ]

        c = TranscriptAnnotation(config)._get_worst_consequence(transcripts)
        assert c == ["NM_12300.3"]

        # Test the different cases in one
        transcripts = [
            {
                "transcript": "NM_12300.3",
                "consequences": ["consequence3", "consequence2", "consequence1"],
            },
            {"transcript": "NM_12301.2", "consequences": []},
            {"transcript": "NM_12302.3", "consequences": ["consequence3", "consequence2"]},
            {"transcript": "NM_12303.3", "consequences": ["consequence1"]},
            {"transcript": "NM_12304.3", "consequences": ["consequence2"]},
        ]

        c = TranscriptAnnotation(config)._get_worst_consequence(transcripts)
        assert c == ["NM_12300.3", "NM_12303.3"]

    def test_custom_annotation_references(self):

        # Test merging references from internal and custom annotation

        annotation = {"references": [{"pubmed_id": 1234, "sources": ["VEP"]}, {"pubmed_id": 4321}]}
        custom_annotation = {
            "references": [
                {"pubmed_id": 9874, "sources": ["User"]},
                {"id": 845, "sources": ["Something"]},
                {"pubmed_id": 1234, "sources": ["User"]},  # Also in annotation
            ]
        }

        result = AnnotationProcessor.process(annotation, custom_annotation=custom_annotation)
        assert len(result["references"]) == 4
        # Fetch the one in both annotations
        in_both_ref = [r for r in result["references"] if r.get("pubmed_id") == 1234]
        assert len(in_both_ref) == 1
        assert "User" in in_both_ref[0]["sources"]
        assert "VEP" in in_both_ref[0]["sources"]
