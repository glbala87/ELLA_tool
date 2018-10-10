"""
Integration/unit test for the AlleleFilter module.
Since it consists mostly of database queries, it's tested on a live database.
"""
import copy
import pytest

from api.allelefilter.consequence_filter import ConsequenceFilter
from vardb.datamodel import allele, annotation, gene, annotationshadow, assessment

import hypothesis as ht
import hypothesis.strategies as st


# prevent screen getting filled with output (useful when testing manually)
#import logging
#logging.getLogger('vardb.deposit.deposit_genepanel').setLevel(logging.CRITICAL)


GLOBAL_CONFIG = {
    'variant_criteria': {
        "splice_region": [-10, 5],
        "utr_region": [-12, 20],
        "consequence_cutoff": "synonymous_variant",
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
    },
    'transcripts': {
        "consequences": [
            "transcript_ablation",
            "splice_donor_variant",
            "splice_acceptor_variant",
            "stop_gained",
            "frameshift_variant",
            "start_lost",
            "initiator_codon_variant",
            "stop_lost",
            "inframe_insertion",
            "inframe_deletion",
            "missense_variant",
            "protein_altering_variant",
            "transcript_amplification",
            "splice_region_variant",
            "incomplete_terminal_codon_variant",
            "synonymous_variant",
            "stop_retained_variant",
            "coding_sequence_variant",
            "mature_miRNA_variant",
            "5_prime_UTR_variant",
            "3_prime_UTR_variant",
            "non_coding_transcript_exon_variant",
            "non_coding_transcript_variant",
            "intron_variant",
            "NMD_transcript_variant",
            "upstream_gene_variant",
            "downstream_gene_variant",
            "TFBS_ablation",
            "TFBS_amplification",
            "TF_binding_site_variant",
            "regulatory_region_variant",
            "regulatory_region_ablation",
            "regulatory_region_amplification",
            "feature_elongation",
            "feature_truncation",
            "intergenic_variant"
        ],
        "severe_consequence_threshold": 'mature_miRNA_variant',
        'inclusion_regex': "NM_.*"
    }
}


@st.composite
def allele_positions(draw, chromosome, start, end):
    start_position = draw(st.integers(min_value=start, max_value=end))
    end_position = draw(st.integers(min_value=start_position+1, max_value=start_position+50))
    return (chromosome, start_position, end_position)


allele_start = 1300


def create_allele(data=None):
    global allele_start
    allele_start += 1
    default_allele_data = {
            "chromosome": "1",
            "start_position": allele_start,
            "open_end_position": allele_start+1,
            "change_from": "A",
            "change_to": "T",
            "change_type": "SNP",
            "vcf_pos": allele_start+1,
            "vcf_ref": "A",
            "vcf_alt": "T"
        }
    if data:
        for k in data:
            default_allele_data[k] = data[k]
    data = default_allele_data

    return allele.Allele(
        genome_reference="GRCh37",
        **data
    )


def create_annotation(annotations, allele=None):
    return annotation.Annotation(
        annotations=annotations,
        allele=allele
    )


def create_allele_with_annotation(session, annotations=None, allele_data=None):
    al = create_allele(data=allele_data)
    session.add(al)
    if annotations is not None:
        an = create_annotation(annotations, allele=al)
        session.add(an)
    else:
        an = None

    return al, an


def create_genepanel(genepanel_config):
    # Create fake genepanel for testing purposes

    g1_ad = gene.Gene(hgnc_id=int(1e6), hgnc_symbol="GENE1AD")
    g1_ar = gene.Gene(hgnc_id=int(2e6), hgnc_symbol="GENE1AR")
    g2 = gene.Gene(hgnc_id=int(3e6), hgnc_symbol="GENE2")
    g3 = gene.Gene(hgnc_id=int(4e6), hgnc_symbol="GENE3")
    g4 = gene.Gene(hgnc_id=int(5e6), hgnc_symbol="GENE4")
    g5 = gene.Gene(hgnc_id=int(6e6), hgnc_symbol="GENE5")

    t1_ad = gene.Transcript(
        gene=g1_ad,
        transcript_name='NM_1AD.1',
        type='RefSeq',
        genome_reference='',
        chromosome='1',
        tx_start=1000,
        tx_end=1500,
        strand='+',
        cds_start=1230,
        cds_end=1430,
        exon_starts=[1100, 1200, 1300, 1400],
        exon_ends=[1160, 1260, 1360, 1460]
    )

    t1_ar = gene.Transcript(
        gene=g1_ar,
        transcript_name='NM_1AR.1',
        type='RefSeq',
        genome_reference='',
        chromosome='1',
        tx_start=1000,
        tx_end=1500,
        strand='+',
        cds_start=1230,
        cds_end=1430,
        exon_starts=[1100, 1200, 1300, 1400],
        exon_ends=[1160, 1260, 1360, 1460]
    )

    t2 = gene.Transcript(
        gene=g2,
        transcript_name='NM_2.1',
        type='RefSeq',
        genome_reference='',
        chromosome='2',
        tx_start=2000,
        tx_end=2500,
        strand='+',
        cds_start=2230,
        cds_end=2430,
        exon_starts=[2100, 2200, 2300, 2400],
        exon_ends=[2160, 2260, 2360, 2460]
    )

    t3 = gene.Transcript(
        gene=g3,
        transcript_name='NM_3.1',
        type='RefSeq',
        genome_reference='',
        chromosome='3',
        tx_start=3000,
        tx_end=3500,
        strand='+',
        cds_start=3230,
        cds_end=3430,
        exon_starts=[3100, 3200, 3300, 3400],
        exon_ends=[3160, 3260, 3360, 3460]
    )

    t4 = gene.Transcript(
        gene=g4,
        transcript_name='NM_4.1',
        type='RefSeq',
        genome_reference='',
        chromosome='4',
        tx_start=4000,
        tx_end=4500,
        strand='+',
        cds_start=4230,
        cds_end=4430,
        exon_starts=[4100, 4200, 4300, 4400],
        exon_ends=[4160, 4260, 4360, 4460]
    )

    t5_reverse = gene.Transcript(
        gene=g5,
        transcript_name='NM_5.1',
        type='RefSeq',
        genome_reference='',
        chromosome='5',
        tx_start=5000,
        tx_end=5500,
        strand='-',
        cds_start=5230,
        cds_end=5430,
        exon_starts=[5100, 5200, 5300, 5400],
        exon_ends=[5160, 5260, 5360, 5460]
    )

    p1 = gene.Phenotype(
        gene=g1_ad,
        inheritance='AD',
        description='P1'
    )

    p2 = gene.Phenotype(
        gene=g1_ar,
        inheritance='AD,AR',
        description='P2'
    )

    genepanel = gene.Genepanel(
        name='testpanel',
        version='v01',
        genome_reference='GRCh37',
        config=genepanel_config
    )

    genepanel.transcripts = [t1_ad, t1_ar, t2, t3, t4, t5_reverse]
    genepanel.phenotypes = [p1, p2]
    return genepanel


class TestConsequenceFilter(object):

    @pytest.mark.aa(order=0)
    def test_prepare_data(self, test_database, session):
        test_database.refresh()  # Reset db

        # We need to recreate the annotation shadow tables,
        # since we want to use our test config
        annotationshadow.create_shadow_tables(session, GLOBAL_CONFIG)

        gp = create_genepanel({})
        session.add(gp)
        session.commit()


    def test_consequence_filter(self, session):

        pa1, _ = create_allele_with_annotation(
            session,
            {
                'transcripts': [
                    {
                        'symbol': 'GENE1AD',
                        'transcript': 'NM_SOMETHING',
                        'consequences': ['synonymous_variant']
                    }
                ]
            }
        )


        pa2, _ = create_allele_with_annotation(
            session,
            {
                'transcripts': [
                    {
                        'symbol': 'GENE1AD',
                        'transcript': 'NM_SOMETHING',
                        'consequences': ['synonymous_variant']
                    },
                    {
                        'symbol': 'GENE1AD',
                        'transcript': 'NOT_NM', # Doesn't match NM_*, shouldn't be considered by filter
                        'consequences': ['frameshift_variant']
                    },

                ]
            }
        )


        pa3, _ = create_allele_with_annotation(
            session,
            {
                'transcripts': [
                    {
                        'symbol': 'GENE1AD',
                        'transcript': 'NM_SOMETHING',
                        'consequences': ['synonymous_variant']
                    },
                    {
                        'symbol': 'SOME_OTHER_GENE',  # Gene not in genepanel, shouldn't be considered by filter
                        'transcript': 'NM_SOMETHING2',
                        'consequences': ['frameshift_variant']
                    },

                ]
            }
        )


        pa4, _ = create_allele_with_annotation(
            session,
            {
                'transcripts': [
                    {
                        'symbol': 'GENE1AD',
                        'transcript': 'NM_SOMETHING',
                        'consequences': ['synonymous_variant']
                    },
                    {
                        'symbol': 'GENE1AR',
                        'transcript': 'NM_SOMETHING2',
                        'consequences': ['upstream_gene_variant'] # Less severe consequence variant, worst consequence is 'synonymous_variant'
                    },

                ]
            }
        )


        session.commit()

        cf = ConsequenceFilter(session, GLOBAL_CONFIG)
        gp_key = ('testpanel', 'v01')
        allele_ids = [pa1.id, pa2.id, pa3.id, pa4.id]
        result = cf.filter_alleles({gp_key: allele_ids})

        assert result[gp_key] == set(allele_ids)


        na1, _ = create_allele_with_annotation(
            session,
            {
                'transcripts': [
                    {
                        'symbol': 'GENE3',
                        'hgnc_id': int(4e6),
                        'transcript': 'NM_SOMETHING2.1',
                        'consequences': ['missense_variant']
                    }
                ],
            },
            None,
        )

        na2, _ = create_allele_with_annotation(
            session,
            {
                'transcripts': [
                    {
                        'symbol': 'GENE3',
                        'hgnc_id': int(4e6),
                        'transcript': 'NM_SOMETHING.1',
                        'consequences': ['synonymous_variant']
                    },
                    {
                        'symbol': 'GENE3',
                        'hgnc_id': int(4e6),
                        'transcript': 'NM_SOMETHING2.1',
                        'consequences': ['frameshift_variant']
                    }
                ],
            },
            None,
        )

        na3, _ = create_allele_with_annotation(
            session,
            {
                'transcripts': [
                    {
                        'symbol': 'GENE3',
                        'hgnc_id': int(4e6),
                        'transcript': 'NM_SOMETHING.1',
                        'consequences': ['synonymous_variant']
                    },
                    {
                        'symbol': 'GENE2', # Different gene, but in the genepanel
                        'hgnc_id': int(3e6),
                        'transcript': 'NM_SOMETHING2.1',
                        'consequences': ['frameshift_variant']
                    }
                ],
            },
            None,
        )

        na4, _ = create_allele_with_annotation(
            session,
            {
                'transcripts': [
                    {
                        'symbol': 'GENE3',
                        'hgnc_id': int(4e6),
                        'transcript': 'NM_SOMETHING.1',
                        'consequences': ['synonymous_variant']
                    },
                    {
                        'symbol': 'GENE2',
                        'hgnc_id': 0, # Wrong hgnc_id shouldn't matter, GENE2 is in the genepanel
                        'transcript': 'NM_SOMETHING2.1',
                        'consequences': ['frameshift_variant']
                    }
                ],
            },
            None,
        )

        na5, _ = create_allele_with_annotation(
            session,
            {
                'transcripts': [
                    {
                        'symbol': 'GENE3',
                        'hgnc_id': int(4e6),
                        'transcript': 'NM_SOMETHING.1',
                        'consequences': ['synonymous_variant']
                    },
                    {
                        'symbol': 'SOME_ALIAS_FOR_GENE2', # Wrong gene name shouldn't matter, hgnc id is in the genepanel
                        'hgnc_id': int(3e6),
                        'transcript': 'NM_SOMETHING2.1',
                        'consequences': ['frameshift_variant']
                    }
                ],
            },
            None,
        )

        # Worst consequence in not equal to 'synonymous_variant' (in practical use, this case will likely be caught by region filter)
        na6, _ = create_allele_with_annotation(
            session,
            {
                'transcripts': [
                    {
                        'symbol': 'GENE3',
                        'hgnc_id': int(4e6),
                        'transcript': 'NM_SOMETHING.1',
                        'consequences': ['upstream_gene_variant']
                    },
                    {
                        'symbol': 'GENE2',
                        'hgnc_id': int(3e6),
                        'transcript': 'NM_SOMETHING2.1',
                        'consequences': ['intron_variant']
                    }
                ],
            },
            None,
        )

        session.commit()

        cf = ConsequenceFilter(session, GLOBAL_CONFIG)
        gp_key = ('testpanel', 'v01')
        allele_ids = [na1.id, na2.id, na3.id, na4.id, na5.id, na6.id]
        result = cf.filter_alleles({gp_key: allele_ids})

        assert not result[gp_key]

