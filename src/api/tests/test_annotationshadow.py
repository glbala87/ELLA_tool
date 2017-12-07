"""
Tests for annotationshadow tables, testing the trigger functionality,
and that they are populated correctly.
"""
import copy
import pytest

from vardb.datamodel import allele, annotation, annotationshadow


GLOBAL_CONFIG = {
    'variant_criteria': {
        "frequencies": {
            "groups": {
                "external": {
                    "ExAC": ["G", "FIN"],
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


def get_freq_column_names():
    names = list()
    for provider, key  in annotationshadow.iter_freq_groups(GLOBAL_CONFIG):
        names.append('{}.{}'.format(provider, key))
    return names


def get_freq_num_column_names():
    names = list()
    for provider, key  in annotationshadow.iter_freq_groups(GLOBAL_CONFIG):
        names.append('{}_num.{}'.format(provider, key))
    return names

allele_start = 0


def create_allele():
    global allele_start
    allele_start += 1
    return allele.Allele(
        genome_reference="GRCh37",
        chromosome="1",
        start_position=allele_start,
        open_end_position=allele_start+1,
        change_from="A",
        change_to="T",
        change_type="SNP",
        vcf_pos=allele_start+1,
        vcf_ref="A",
        vcf_alt="T"
    )


def create_annotation(annotations, allele=None):
    return annotation.Annotation(
        annotations=annotations,
        allele=allele
    )


def create_allele_with_annotation(session, annotations):
    al = create_allele()
    an = create_annotation(annotations, allele=al)
    session.add(al)
    session.add(an)
    return al, an


class TestAnnotationShadow(object):

    @pytest.mark.aa(order=0)
    def test_prepare_data(self, test_database, session):
        test_database.refresh()  # Reset db

        # We need to recreate the annotation shadow tables,
        # since we want to use our test config
        annotationshadow.create_shadow_tables(session, GLOBAL_CONFIG)

        columns = [i[0] for i in session.execute("""
            SELECT column_name
            FROM information_schema.columns
            WHERE table_schema = 'public'
            AND table_name   = 'annotationshadowfrequency'
        """)]

        for name in get_freq_column_names():
            assert name in columns

        for name in get_freq_num_column_names():
            assert name in columns

        session.commit()

    @pytest.mark.aa(order=1)
    def test_annotationshadowcreate(self, session):

        a1_annotation = {
            'frequencies': {
                'ExAC': {
                    'freq': {
                        'G': 0.0051
                    },
                    'num': {
                        'G': 9000
                    }
                }
            },
            'transcripts': [
                {
                    'symbol': 'GENE1AD',
                    'transcript': 'NM_1.1',
                    'HGVSc_short': 'c.123A>G',
                    'protein': 'NP_SOMETHING',
                    'HGVSp_short': 'p.Arg123Gly',
                    'consequences': ['CONSEQUENCE1', 'CONSEQUENCE2'],
                    'exon_distance': 0
                }
            ]
        }
        a1, an1 = create_allele_with_annotation(session, a1_annotation)

        session.add(a1)
        session.commit()

        ast1 = session.query(annotationshadow.AnnotationShadowTranscript).filter(
            annotationshadow.AnnotationShadowTranscript.allele_id == a1.id
        ).one()

        assert ast1.allele_id == an1.allele_id
        assert ast1.symbol == an1.annotations['transcripts'][0]['symbol']
        assert ast1.transcript == an1.annotations['transcripts'][0]['transcript']
        assert ast1.hgvsc == an1.annotations['transcripts'][0]['HGVSc_short']
        assert ast1.protein == an1.annotations['transcripts'][0]['protein']
        assert ast1.hgvsp == an1.annotations['transcripts'][0]['HGVSp_short']
        assert ast1.hgvsp == an1.annotations['transcripts'][0]['HGVSp_short']
        assert ast1.consequences == an1.annotations['transcripts'][0]['consequences']
        assert ast1.exon_distance == an1.annotations['transcripts'][0]['exon_distance']

        asf1 = session.query(annotationshadow.AnnotationShadowFrequency).filter(
            annotationshadow.AnnotationShadowFrequency.allele_id == a1.id
        ).one()

        assert asf1.allele_id == an1.allele_id

        for name in get_freq_column_names():
            assert hasattr(asf1, name)
            if name == 'ExAC.G':
                assert getattr(asf1, 'ExAC.G') == a1_annotation['frequencies']['ExAC']['freq']['G']
            else:
                assert getattr(asf1, name) is None

        for name in get_freq_num_column_names():
            assert hasattr(asf1, name)
            if name == 'ExAC_num.G':
                assert getattr(asf1, 'ExAC_num.G') == a1_annotation['frequencies']['ExAC']['num']['G']
            else:
                assert getattr(asf1, name) is None

        # Multiple transcripts, no frequency
        a2_annotation = {
            'transcripts': [
                {
                    'symbol': 'GENE2',
                    'transcript': 'NM_2.1',
                    'HGVSc_short': 'c.123A>G',
                    'protein': 'NP_SOMETHING',
                    'HGVSp_short': 'p.Arg123Gly',
                    'consequences': ['CONSEQUENCE1', 'CONSEQUENCE2'],
                    'exon_distance': 0
                },
                {
                    'transcript': 'NM_1.1'
                }
            ]
        }

        a2, an2 = create_allele_with_annotation(session, a2_annotation)

        session.add(a2)
        session.commit()

        ast2 = session.query(annotationshadow.AnnotationShadowTranscript).filter(
            annotationshadow.AnnotationShadowTranscript.allele_id == a2.id
        ).all()

        assert len(ast2) == 2

        assert ast2[0].allele_id == an2.allele_id
        assert ast2[0].symbol == an2.annotations['transcripts'][0]['symbol']
        assert ast2[0].transcript == an2.annotations['transcripts'][0]['transcript']
        assert ast2[0].hgvsc == an2.annotations['transcripts'][0]['HGVSc_short']
        assert ast2[0].protein == an2.annotations['transcripts'][0]['protein']
        assert ast2[0].hgvsp == an2.annotations['transcripts'][0]['HGVSp_short']
        assert ast2[0].consequences == an2.annotations['transcripts'][0]['consequences']
        assert ast2[0].exon_distance == an2.annotations['transcripts'][0]['exon_distance']

        assert ast2[1].allele_id == an2.allele_id
        assert ast2[1].transcript == 'NM_1.1'
        assert ast2[1].symbol is None
        assert ast2[1].hgvsc is None
        assert ast2[1].protein is None
        assert ast2[1].hgvsp is None
        assert ast2[1].hgvsp is None
        assert ast2[1].consequences == list()
        assert ast2[1].exon_distance is None

        asf2 = session.query(annotationshadow.AnnotationShadowFrequency).filter(
            annotationshadow.AnnotationShadowFrequency.allele_id == a2.id
        ).one()

        assert asf2.allele_id == an2.allele_id

        for name in get_freq_column_names():
            assert hasattr(asf2, name)
            assert getattr(asf2, name) is None

        for name in get_freq_num_column_names():
            assert hasattr(asf2, name)
            assert getattr(asf2, name) is None

        # No transcripts -> no rows in AnnotationShadowTranscripts
        a3_annotation = {
            'transcripts': []
        }

        a3, an3 = create_allele_with_annotation(session, a3_annotation)

        session.add(a3)
        session.commit()

        ast3 = session.query(annotationshadow.AnnotationShadowTranscript).filter(
            annotationshadow.AnnotationShadowTranscript.allele_id == a3.id
        ).all()

        assert len(ast3) == 0
