from datalayer.alleledataloader.annotationprocessor import TranscriptAnnotation


def test_get_worse_consequence():
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
