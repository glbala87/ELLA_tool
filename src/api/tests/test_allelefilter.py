"""
Integration/unit test for the AlleleFilter module.
Since it consists mostly of database queries, it's tested on a live database.
"""
import copy
import pytest

from api.allelefilter import AlleleFilter
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
        "freq_num_thresholds": {
            "ExAC": {
                "G": 2000,
                "FIN": 2000,
            }
        },
        "genepanel_config": {
            "freq_cutoff_groups": {
                "AD": {
                    "external": {
                        "hi_freq_cutoff": 0.005,
                        "lo_freq_cutoff": 0.001
                    },
                    "internal": {
                        "hi_freq_cutoff": 0.05,
                        "lo_freq_cutoff": 0.01
                    }
                },
                "default": {
                    "external": {
                        "hi_freq_cutoff": 0.30,
                        "lo_freq_cutoff": 0.1
                    },
                    "internal": {
                        "hi_freq_cutoff": 0.05,
                        "lo_freq_cutoff": 0.01
                    }
                }
            }
        },
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
    "classification": {
        "options": [  # Also defines sorting order
            {
                "name": "Class 1",
                "value": "1"
            },
            {
                "name": "Class 2",
                "value": "2",
                "outdated_after_days": 180,  # Marked as outdated after N number of days
                "exclude_filtering_existing_assessment": True
            },
            {
                "name": "Class 3",
                "value": "3",
                "outdated_after_days": 180,
                "exclude_filtering_existing_assessment": True
            },
            {
                "name": "Class 4",
                "value": "4",
                "outdated_after_days": 180,
                "exclude_filtering_existing_assessment": True
            },
            {
                "name": "Class 5",
                "value": "5",
                "outdated_after_days": 180,
                "exclude_filtering_existing_assessment": True
            }
        ]
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

THRESHOLD_1000 = {
        "freq_num_thresholds": {
            "ExAC": {
                "G": 1000,
                "AFR": 1000,
                "AMR": 1000,
                "EAS": 1000,
                "FIN": 1000,
                "NFE": 1000,
                "OTH": 1000,
                "SAS": 1000
            }
        }
}


GENEPANEL_CONFIG = {
    'data': {
        'genes': {
            'GENE2': {
                "freq_cutoffs": {
                    "external": {
                        "hi_freq_cutoff": 0.5,
                        "lo_freq_cutoff": 0.1
                    },
                    "internal": {
                        "hi_freq_cutoff": 0.7,
                        "lo_freq_cutoff": 0.6
                    }
                }
            },
            'GENE4': {
                "freq_cutoffs": {
                    "external": {
                        "hi_freq_cutoff": 1e-12,
                        "lo_freq_cutoff": 1e-12
                    },
                    "internal": {
                        "hi_freq_cutoff": 1e-12,
                        "lo_freq_cutoff": 1e-12
                    }
                }
            }
        }
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

def create_assessment(session, classification, allele=None):
    assmt = assessment.AlleleAssessment(
        classification=classification,
        allele=allele,
        genepanel_name="testpanel",
        genepanel_version="v01"
    )
    session.add(assmt)
    return assmt

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


def create_error_message(allele_ids, allele_info):
    uniq_ids = list(set(allele_ids))
    msg = ""
    for a_id in uniq_ids:
        a, anno = allele_info[a_id]
        msg += "\nAllele {} has annotation\n".format(a_id)
        msg += str(anno)
    return msg


class TestAlleleFilter(object):

    @pytest.mark.aa(order=0)
    def test_prepare_data(self, test_database, session):
        test_database.refresh()  # Reset db

        # We need to recreate the annotation shadow tables,
        # since we want to use our test config
        annotationshadow.create_shadow_tables(session, GLOBAL_CONFIG)

        gp = create_genepanel(GENEPANEL_CONFIG)
        session.add(gp)
        session.commit()


    @pytest.mark.aa(order=1)
    def test_filter_order(self, session):
        # Test filter order: gene -> frequency -> region

        # Would be filtered on frequency, gene and region
        a1, _ = create_allele_with_annotation(session,
            {
                'frequencies': {
                    'ExAC': {
                        'freq': {
                            'G': 0.0051   # Above 0.005
                        },
                        'num': {
                            'G': 9000  # Above 2000
                        }
                    }
                },
                'transcripts': [
                    {
                        'symbol': 'GENE3',
                        'hgnc_id': int(4e6),
                        'transcript': 'NM_3.1',
                        'exon_distance': 1000
                    }
                ]
            },
            {
                "chromosome": "ORDER"
            }
        )

        # Would be filtered on frequency and region
        a2, _ = create_allele_with_annotation(session,
            {
                'frequencies': {
                    'ExAC': {
                        'freq': {
                            'G': 0.31   # Above 0.3
                        },
                        'num': {
                            'G': 9000  # Above 2000
                        }
                    }
                },
                'transcripts': [
                    {
                        'symbol': 'GENE1',
                        'hgnc_id': int(1e6),
                        'transcript': 'NM_1AR.1',
                        'exon_distance': 1000
                    }
                ]
            },
            {
                "chromosome": "ORDER"
            }
        )

        # Would be filtered on region only
        a3, _ = create_allele_with_annotation(session,
            {
                'frequencies': {
                    'ExAC': {
                        'freq': {
                            'G': 0   # BELOW 0.3
                        },
                        'num': {
                            'G': 9000  # Above 2000
                        }
                    }
                },
                'transcripts': [
                    {
                        'symbol': 'GENE2',
                        'hgnc_id': int(3e6),
                        'transcript': 'NM_2.1',
                        'exon_distance': 1000
                    }
                ]
            },
            {
                "chromosome": "ORDER"
            }
        )

        session.commit()

        af = AlleleFilter(session, GLOBAL_CONFIG)
        gp_key = ('testpanel', 'v01')
        allele_ids = [a1.id, a2.id, a3.id]
        result = af.filter_alleles({gp_key: allele_ids})

        # filtered based on gene symbol is defined relevant: done in pipeline
        # assert a1.id in result[gp_key]['excluded_allele_ids']['gene']
        # assert a2.id not in result[gp_key]['excluded_allele_ids']['gene']
        # assert a3.id not in result[gp_key]['excluded_allele_ids']['gene']

        assert a2.id in result[gp_key]['excluded_allele_ids']['frequency']
        assert a1.id not in result[gp_key]['excluded_allele_ids']['frequency']
        assert a3.id not in result[gp_key]['excluded_allele_ids']['frequency']

        assert a3.id in result[gp_key]['excluded_allele_ids']['region']
        assert a1.id in result[gp_key]['excluded_allele_ids']['region']
        assert a2.id not in result[gp_key]['excluded_allele_ids']['region']

        assert a1.id not in result[gp_key]['allele_ids']
        assert a2.id not in result[gp_key]['allele_ids']
        assert a3.id not in result[gp_key]['allele_ids']

    @pytest.mark.aa(order=2)
    def test_classification_filter(self, session):
        a1, a1anno = create_allele_with_annotation(session,
            {
                'frequencies': {
                    'ExAC': {
                        'freq': {
                            'G': 0.0051   # Above 0.005
                        },
                        'num': {
                            'G': 9000  # Above 2000
                        }
                    }
                },
                'transcripts': [
                    {
                        'symbol': 'GENE1AD',
                        'hgnc_id': int(1e6),
                        'transcript': 'NM_1AD.1',
                        'exon_distance': 0
                    }
                ]
            }
        )

        a2, _ = create_allele_with_annotation(session,
            None,
            {
                "chromosome": "OUTSIDE_TRANSCRIPT",
                "start_position": 1,
                "open_end_position": 2,
            }
        )

        a3, _ = create_allele_with_annotation(session,
            None,
            {
                "chromosome": "ALSO_OUTSIDE_TRANSCRIPT",
                "start_position": 1,
                "open_end_position": 2,
            }
        )

        session.flush()

        af = AlleleFilter(session, GLOBAL_CONFIG)
        gp_key = ('testpanel', 'v01')
        allele_ids = [a1.id, a2.id, a3.id]
        result = af.filter_alleles({gp_key: allele_ids})
        assert set(result[gp_key]['excluded_allele_ids']['frequency']) == set([a1.id])
        assert set(result[gp_key]['excluded_allele_ids']['region']) == set([a2.id, a3.id])
        assert set(result[gp_key]['allele_ids']) == set()

        create_assessment(session, '3', a1)
        create_assessment(session, '2', a2)
        create_assessment(session, '1', a3)  # Class 1 are not excluded from filtering

        session.flush()
        result = af.filter_alleles({gp_key: allele_ids})
        assert set(result[gp_key]['excluded_allele_ids']['frequency']) == set()
        assert set(result[gp_key]['excluded_allele_ids']['region']) == set([a3.id])
        assert set(result[gp_key]['allele_ids']) == set([a1.id, a2.id])
