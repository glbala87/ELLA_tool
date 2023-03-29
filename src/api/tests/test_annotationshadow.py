"""
Tests for annotationshadow tables, testing the trigger functionality,
and that they are populated correctly.
"""
import pytest

from vardb.datamodel import annotationshadow
from conftest import mock_allele_with_annotation


GLOBAL_CONFIG = {
    "frequencies": {
        "groups": {
            "external": {"ExAC": ["G", "FIN"], "1000g": ["G"], "esp6500": ["AA", "EA"]},
            "internal": {"inDB": ["AF"]},
        }
    }
}


def get_freq_column_names():
    names = list()
    for provider, key in annotationshadow.iter_freq_groups(GLOBAL_CONFIG["frequencies"]["groups"]):
        names.append("{}.{}".format(provider, key))
    return names


def get_freq_num_column_names():
    names = list()
    for provider, key in annotationshadow.iter_freq_groups(GLOBAL_CONFIG["frequencies"]["groups"]):
        names.append("{}_num.{}".format(provider, key))
    return names


@pytest.fixture(autouse=True)
def setup(test_database, session):
    test_database.refresh()  # Reset db

    # We need to recreate the annotation shadow tables,
    # since we want to use our test config
    # Delete existing filterconfigs and usergroups to avoid errors
    # when creating new shadow tables
    session.execute("DELETE FROM usergroupfilterconfig")
    session.execute("DELETE FROM filterconfig")
    session.execute("UPDATE usergroup SET config='{}'")
    annotationshadow.create_shadow_tables(session, GLOBAL_CONFIG)
    session.commit()


def test_prepare_data(session):
    columns = [
        i[0]
        for i in session.execute(
            """
        SELECT column_name
        FROM information_schema.columns
        WHERE table_schema = 'public'
        AND table_name   = 'annotationshadowfrequency'
    """
        )
    ]

    for name in get_freq_column_names():
        assert name in columns

    for name in get_freq_num_column_names():
        assert name in columns

    session.commit()


def test_annotationshadowcreate(session):
    a1_annotation = {
        "frequencies": {"ExAC": {"freq": {"G": 0.0051}, "num": {"G": 9000}}},
        "transcripts": [
            {
                "symbol": "GENE1AD",
                "transcript": "NM_1.1",
                "HGVSc": "c.123A>G",
                "protein": "NP_SOMETHING",
                "HGVSp": "p.Arg123Gly",
                "consequences": ["intron_variant", "splice_region_variant"],
                "exon_distance": 0,
            }
        ],
    }
    a1, an1 = mock_allele_with_annotation(session, annotations=a1_annotation)

    session.add(a1)
    session.commit()

    ast1 = (
        session.query(annotationshadow.AnnotationShadowTranscript)
        .filter(annotationshadow.AnnotationShadowTranscript.allele_id == a1.id)
        .one()
    )

    assert ast1.allele_id == an1.allele_id
    assert ast1.symbol == an1.annotations["transcripts"][0]["symbol"]
    assert ast1.transcript == an1.annotations["transcripts"][0]["transcript"]
    assert ast1.hgvsc == an1.annotations["transcripts"][0]["HGVSc"]
    assert ast1.protein == an1.annotations["transcripts"][0]["protein"]
    assert ast1.hgvsp == an1.annotations["transcripts"][0]["HGVSp"]
    assert ast1.consequences == an1.annotations["transcripts"][0]["consequences"]
    assert ast1.exon_distance == an1.annotations["transcripts"][0]["exon_distance"]

    asf1 = (
        session.query(annotationshadow.AnnotationShadowFrequency)
        .filter(annotationshadow.AnnotationShadowFrequency.allele_id == a1.id)
        .one()
    )

    assert asf1.allele_id == an1.allele_id

    for name in get_freq_column_names():
        assert hasattr(asf1, name)
        if name == "ExAC.G":
            assert getattr(asf1, "ExAC.G") == a1_annotation["frequencies"]["ExAC"]["freq"]["G"]
        else:
            assert getattr(asf1, name) is None

    for name in get_freq_num_column_names():
        assert hasattr(asf1, name)
        if name == "ExAC_num.G":
            assert getattr(asf1, "ExAC_num.G") == a1_annotation["frequencies"]["ExAC"]["num"]["G"]
        else:
            assert getattr(asf1, name) is None

    # Multiple transcripts, no frequency
    a2_annotation = {
        "transcripts": [
            {
                "symbol": "GENE2",
                "transcript": "NM_2.1",
                "HGVSc": "c.123A>G",
                "protein": "NP_SOMETHING",
                "HGVSp": "p.Arg123Gly",
                "strand": 1,
                "consequences": ["intron_variant", "splice_region_variant"],
                "exon_distance": 0,
            },
            {"transcript": "NM_1.1", "is_canonical": True, "in_last_exon": "no", "strand": 1},
        ]
    }

    a2, an2 = mock_allele_with_annotation(session, annotations=a2_annotation)

    session.add(a2)
    session.commit()

    ast2 = (
        session.query(annotationshadow.AnnotationShadowTranscript)
        .filter(annotationshadow.AnnotationShadowTranscript.allele_id == a2.id)
        .all()
    )

    assert len(ast2) == 2

    assert ast2[0].allele_id == an2.allele_id
    assert ast2[0].symbol == an2.annotations["transcripts"][0]["symbol"]
    assert ast2[0].transcript == an2.annotations["transcripts"][0]["transcript"]
    assert ast2[0].hgvsc == an2.annotations["transcripts"][0]["HGVSc"]
    assert ast2[0].protein == an2.annotations["transcripts"][0]["protein"]
    assert ast2[0].hgvsp == an2.annotations["transcripts"][0]["HGVSp"]
    assert ast2[0].consequences == an2.annotations["transcripts"][0]["consequences"]
    assert ast2[0].exon_distance == an2.annotations["transcripts"][0]["exon_distance"]

    assert ast2[1].allele_id == an2.allele_id
    assert ast2[1].transcript == "NM_1.1"
    assert ast2[1].symbol is None
    assert ast2[1].hgvsc is None
    assert ast2[1].protein is None
    assert ast2[1].hgvsp is None
    assert ast2[1].consequences == list()
    assert ast2[1].exon_distance is None

    asf2 = (
        session.query(annotationshadow.AnnotationShadowFrequency)
        .filter(annotationshadow.AnnotationShadowFrequency.allele_id == a2.id)
        .one()
    )

    assert asf2.allele_id == an2.allele_id

    for name in get_freq_column_names():
        assert hasattr(asf2, name)
        assert getattr(asf2, name) is None

    for name in get_freq_num_column_names():
        assert hasattr(asf2, name)
        assert getattr(asf2, name) is None

    # No transcripts -> no rows in AnnotationShadowTranscripts
    a3_annotation = {"transcripts": []}

    a3, an3 = mock_allele_with_annotation(session, annotations=a3_annotation)

    session.add(a3)
    session.commit()

    ast3 = (
        session.query(annotationshadow.AnnotationShadowTranscript)
        .filter(annotationshadow.AnnotationShadowTranscript.allele_id == a3.id)
        .all()
    )

    assert len(ast3) == 0
