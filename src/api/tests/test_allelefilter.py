"""
Integration/unit test for the AlleleFilter module.
Since it consists mostly of database queries, it's tested on a live database.
"""
import copy
import pytest

from api.util.allelefilter import AlleleFilter
from vardb.datamodel import allele, annotation, gene

# prevent screen getting filled with output (useful when testing manually)
#import logging
#logging.getLogger('vardb.deposit.deposit_genepanel').setLevel(logging.CRITICAL)


GLOBAL_CONFIG = {
    'variant_criteria': {
        "intronic_region": [-10, 5],
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
                "name": "Technical",
                "value": "T",
                "exclude_filtering_existing_assessment": True  # If there's an existing alleleassessment, exclude the allele from being filtered.
            },
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
            }
    }
    }
}


def global_with_overridden_threshold(initial, override):
    return copy.deepcopy(initial).update(override)


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
    return al


def create_allele_with_annotation_tuple(session, annotations):
    al = create_allele()
    an = create_annotation(annotations, allele=al)
    session.add(al)
    session.add(an)
    return al, an


def create_genepanel(genepanel_config):
    # Create fake genepanel for testing purposes

    g1_ad = gene.Gene(hgnc_id=1, hgnc_symbol="GENE1AD")
    g1_ar = gene.Gene(hgnc_id=2, hgnc_symbol="GENE1AR")
    g2 = gene.Gene(hgnc_id=3, hgnc_symbol="GENE2")
    g3 = gene.Gene(hgnc_id=4, hgnc_symbol="GENE3")

    t1_ad = gene.Transcript(
        gene=g1_ad,
        transcript_name='NM_1AD.1',
        type='RefSeq',
        genome_reference='123',
        chromosome='123',
        tx_start=123,
        tx_end=123,
        strand='+',
        cds_start=123,
        cds_end=123,
        exon_starts=[123, 321],
        exon_ends=[123, 321]
    )

    t1_ar = gene.Transcript(
        gene=g1_ar,
        transcript_name='NM_1AR.1',
        type='RefSeq',
        genome_reference='123',
        chromosome='123',
        tx_start=123,
        tx_end=123,
        strand='+',
        cds_start=123,
        cds_end=123,
        exon_starts=[123, 321],
        exon_ends=[123, 321]
    )

    t2 = gene.Transcript(
        gene=g2,
        transcript_name='NM_2.1',
        type='RefSeq',
        genome_reference='123',
        chromosome='123',
        tx_start=123,
        tx_end=123,
        strand='+',
        cds_start=123,
        cds_end=123,
        exon_starts=[123, 321],
        exon_ends=[123, 321]
    )

    t3 = gene.Transcript(
        gene=g3,
        transcript_name='NM_3.1',
        type='RefSeq',
        genome_reference='123',
        chromosome='123',
        tx_start=123,
        tx_end=123,
        strand='+',
        cds_start=123,
        cds_end=123,
        exon_starts=[123, 321],
        exon_ends=[123, 321]
    )

    p1 = gene.Phenotype(
        gene=g1_ad,
        genepanel_name='testpanel',
        genepanel_version='v01',
        inheritance='AD',
        description=''
    )

    p2 = gene.Phenotype(
        gene=g1_ar,
        genepanel_name='testpanel',
        genepanel_version='v01',
        inheritance='AD,AR',
        description=''
    )

    genepanel = gene.Genepanel(
        name='testpanel',
        version='v01',
        genome_reference='GRCh37',
        config=genepanel_config
    )

    genepanel.transcripts = [t1_ad, t1_ar, t2, t3]
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

        gp = create_genepanel(GENEPANEL_CONFIG)
        session.add(gp)
        session.commit()

    @pytest.mark.aa(order=1)
    def test_commonness(self, session):

        # Filter config should end up being the following
        # (GENE2 has override in genepanel config, hence different threshold)
        # GENE1AD: external: 0.005/0.001 , internal: 0.05/0.01
        # GENE1AR: external: 0.30/0.01 , internal: 0.05/0.01
        # GENE2: external: 0.5/0.1 , internal: 0.7/0.6

        ##
        # Test the different commonness groups
        ##

        # Test common

        # GENE1AD: external: 0.005/0.001 , internal: 0.05/0.01
        a1ad = create_allele_with_annotation(session, {
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
                    'transcript': 'NM_1AD.1',
                    'exon_distance': 0
                }
            ]
        })

        # Test less_common

        # GENE1AR: external: 0.30/0.1 , internal: 0.05/0.01
        a1ar = create_allele_with_annotation(session, {
            'frequencies': {
                'ExAC': {
                    'freq': {
                        'G': 0.25   # Between 0.3 and 0.1
                    },
                    'num': {
                        'G': 9000  # Above 2000
                    }
                }
            },
            'transcripts': [
                {
                    'symbol': 'GENE1AR',
                    'transcript': 'NM_1AR.1',
                    'exon_distance': 0
                }
            ]
        })

        # DOESNT_EXIST: should give 'default' group, since no connected 'AR' phenotype
        # external: 0.30/0.1 , internal: 0.05/0.01
        a1nogene = create_allele_with_annotation(session, {
            'frequencies': {
                'ExAC': {
                    'freq': {
                        'G': 0.001  # Less than 0.1
                    },
                    'num': {
                        'G': 9000  # Above 2000
                    }
                }
            },
            'transcripts': [
                {
                    'symbol': 'DOESNT_EXIST',
                    'transcript': 'DOESNT_EXIST',
                    'exon_distance': 0
                }
            ]
        })

        # Test null_freq

        a1nofreq = create_allele_with_annotation(session, {
            'frequencies': {},
            'transcripts': [
                {
                    'symbol': 'DOESNT_EXIST',
                    'transcript': 'DOESNT_EXIST',
                    'exon_distance': 0
                }
            ]
        })

        session.commit()

        af = AlleleFilter(session, GLOBAL_CONFIG)
        gp_key = ('testpanel', 'v01')
        allele_info = [a1ad.id, a1ar.id, a1nogene.id, a1nofreq.id]
        result = af.get_commonness_groups({gp_key: allele_info})

        assert set(result[gp_key]['common']) == set([a1ad.id])
        assert set(result[gp_key]['less_common']) == set([a1ar.id])
        assert set(result[gp_key]['low_freq']) == set([a1nogene.id])
        assert set(result[gp_key]['null_freq']) == set([a1nofreq.id])

        ##
        # Test num thresholds
        ##

        # Test below threshold, one source
        anum1, anum1anno = create_allele_with_annotation_tuple(session, {
            'frequencies': {
                'ExAC': {
                    'freq': {
                        'G': 0.0051   # Above 0.005
                    },
                    'num': {
                        'G': 1999  # Below 2000
                    }
                }
            },
            'transcripts': [
                {
                    'symbol': 'GENE1AD',
                    'transcript': 'NM_1AD.1',
                    'exon_distance': 0
                }
            ]
        })

        # Test threshold, two sources, one above one below
        anum2, anum2anno = create_allele_with_annotation_tuple(session, {
            'frequencies': {
                'ExAC': {
                    'freq': {
                        'G': 0.0051,   # Above 0.005
                        'FIN': 0.0051   # Above 0.005
                    },
                    'num': {
                        'G': 1999,  # Below 2000
                        'FIN': 2000  # Equal 2000
                    }
                },
                '1000g': {
                    'freq': {
                        'G': 0.01   # Above 0.005
                    }
                }
            },
            'transcripts': [
                {
                    'symbol': 'GENE1AD',
                    'transcript': 'NM_1AD.1',
                    'exon_distance': 0
                }
            ]
        })

        # Test below threshold, two sources, one without num threshold filtering
        anum3, anum3anno = create_allele_with_annotation_tuple(session, {
            'frequencies': {
                'ExAC': {
                    'freq': {
                        'G': 0.0051   # Above 0.005
                    },
                    'num': {
                        'G': 1999  # Below 2000
                    }
                },
                '1000g': {
                    'freq': {
                        'G': 0.01   # Above 0.005
                    }
                }
            },
            'transcripts': [
                {
                    'symbol': 'GENE1AD',
                    'transcript': 'NM_1AD.1',
                    'exon_distance': 0
                }
            ]
        })

        # Test gene specific cutoff override
        anum4,anum4anno = create_allele_with_annotation_tuple(session, {
            'frequencies': {
                'ExAC': {
                    'freq': {
                        'G': 0.6   # Above 0.5
                    },
                    'num': {
                        'G': 2001  # Above 2000
                    }
                }
            },
            'transcripts': [
                {
                    'symbol': 'GENE2', # cutoff override for this gene defined in the config of the genepanel
                    'transcript': 'NM_2.1',
                    'exon_distance': 0
                }
            ]
        })

        session.commit()

        af = AlleleFilter(session, GLOBAL_CONFIG)
        gp_key = ('testpanel', 'v01')
        allele_info = {anum1.id: (anum1, anum1anno),
                      anum2.id: (anum2, anum2anno),
                      anum3.id: (anum3, anum3anno),
                      anum4.id: (anum4, anum4anno)}
        result = af.get_commonness_groups({gp_key: allele_info.keys()})

        assert set(result[gp_key]['num_threshold']) == set([anum1.id]),\
            create_error_message(result[gp_key]['num_threshold'], allele_info)

        assert set(result[gp_key]['common']) == set([anum2.id, anum3.id, anum4.id]), \
            create_error_message(result[gp_key]['common'], allele_info)


        del allele_info

        ##
        # Test ordering
        #
        # One allele should only appear in one group,
        # even if the different frequencies would give
        # hits in different ones
        ##
        a2common = create_allele_with_annotation(session, {
            'frequencies': {
                'ExAC': {
                    'freq': {
                        'G': 0.0051   # Above 0.005 -> common
                    },
                    'num': {
                        'G': 9000  # Above 2000
                    }
                },
                '1000g': {
                    'freq': {
                        'G': 0.0001   # Below 0.001 -> low_freq
                    }
                }
            },
            'transcripts': [
                {
                    'symbol': 'GENE1AD',
                    'transcript': 'NM_1AD.1',
                    'exon_distance': 0
                }
            ]
        })

        session.commit()
        gp_key = ('testpanel', 'v01')
        allele_info = [a2common.id]
        result = af.get_commonness_groups({gp_key: allele_info})

        assert result[gp_key]['common'] == [a2common.id]
        assert not result[gp_key]['less_common']
        assert not result[gp_key]['low_freq']
        assert not result[gp_key]['null_freq']

        a2less_common = create_allele_with_annotation(session, {
            'frequencies': {
                'ExAC': {
                    'freq': {
                        'G': 0.002   # Between 0.005 and 0.001 -> less_common
                    },
                    'num': {
                        'G': 9000  # Above 2000
                    }
                },
                '1000g': {
                    'freq': {
                        'G': 0.0001   # Below 0.001 -> low_freq
                    }
                }
            },
            'transcripts': [
                {
                    'symbol': 'GENE1AD',
                    'transcript': 'NM_1AD.1',
                    'exon_distance': 0
                }
            ]
        })

        session.commit()
        gp_key = ('testpanel', 'v01')
        allele_info = [a2less_common.id]
        result = af.get_commonness_groups({gp_key: allele_info})

        assert not result[gp_key]['common']
        assert result[gp_key]['less_common'] == [a2less_common.id]
        assert not result[gp_key]['low_freq']
        assert not result[gp_key]['null_freq']

        a2low_freq = create_allele_with_annotation(session, {
            'frequencies': {
                'ExAC': {
                    'freq': {
                        'G': 0.0001   # Below 0.001 -> low_freq
                    },
                    'num': {
                        'G': 9000  # Above 2000
                    }
                }
                # All other missing freqs will give hits in low_freq
            },
            'transcripts': [
                {
                    'symbol': 'GENE1AD',
                    'transcript': 'NM_1AD.1',
                    'exon_distance': 0
                }
            ]
        })

        session.commit()
        gp_key = ('testpanel', 'v01')
        allele_info = [a2low_freq.id]
        result = af.get_commonness_groups({gp_key: allele_info})

        assert not (result[gp_key]['common'])
        assert not result[gp_key]['less_common']
        assert result[gp_key]['low_freq'] == [a2low_freq.id]
        assert not result[gp_key]['null_freq']

    @pytest.mark.aa(order=2)
    def test_frequency_filtering(self, session):

        # Filter config should end up being the following
        # (GENE2 has override in genepanel config, hence different threshold)
        # GENE1AD: external: 0.005/0.001 , internal: 0.05/0.01
        # GENE1AR: external: 0.30/0.01 , internal: 0.05/0.01
        # GENE2: external: 0.5/0.1 , internal: 0.7/0.6
        # GENE3: Will be 'GENE' filtered

        ##
        # Test positive cases
        ##

        # Test external

        # GENE1AD: external: 0.005/0.001 , internal: 0.05/0.01
        (pa1ad, pa1adanno) = create_allele_with_annotation_tuple(session, {
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
                    'transcript': 'NM_1AD.1',
                    'exon_distance': 0
                }
            ]
        })

        # GENE1AR: external: 0.30/0.1 , internal: 0.05/0.01
        (pa1ar,pa1aranno) = create_allele_with_annotation_tuple(session, {
            'frequencies': {
                'ExAC': {
                    'freq': {
                        'G': 0.31   # Above 0.30
                    },
                    'num': {
                        'G': 9000  # Above 2000
                    }
                }
            },
            'transcripts': [
                {
                    'symbol': 'GENE1AR',
                    'transcript': 'NM_1AR.1',
                    'exon_distance': 0
                }
            ]
        })

        # DOESNT_EXIST: should give 'default' group, since no connected 'AR' phenotype
        # external: 0.30/0.1 , internal: 0.05/0.01
        (pa1nogene, pa1nogeneanno) = create_allele_with_annotation_tuple(session, {
            'frequencies': {
                'ExAC': {
                    'freq': {
                        'G': 0.31   # Above 0.30
                    },
                    'num': {
                        'G': 9000  # Above 2000
                    }
                }
            },
            'transcripts': [
                {
                    'symbol': 'DOESNT_EXIST',
                    'transcript': 'DOESNT_EXIST',
                    'exon_distance': 0
                }
            ]
        })

        # Test internal
        # GENE2: external: 0.5/0.1 , internal: 0.7/0.6
        (pa2, pa2anno) = create_allele_with_annotation_tuple(session, {
            'frequencies': {
                'inDB': {
                    'freq': {
                        'AF': 0.71  # Above 0.7
                    }
                }
            },
            'transcripts': [
                {
                    'symbol': 'GENE2',
                    'transcript': 'NM_2.1',
                    'exon_distance': 0
                }
            ]
        })

        # Test conflicting external/internal
        # GENE1AD: external: 0.005/0.001 , internal: 0.05/0.01
        (pa3,pa3anno)  = create_allele_with_annotation_tuple(session, {
            'frequencies': {
                'ExAC': {
                    'freq': {
                        'G': 0.0051  # Above 0.005
                    },
                    'num': {
                        'G': 9000  # Above 2000
                    }
                },
                'inDB': {
                    'freq': {
                        'AF': 0.000001  # Below 0.05
                    }
                }
            },
            'transcripts': [
                {
                    'symbol': 'GENE1AD',
                    'transcript': 'NM_1AD.1',
                    'exon_distance': 0
                }
            ]
        })

        # Test right on threshold
        # GENE1AD: external: 0.005/0.001 , internal: 0.05/0.01
        (pa4, pa4anno) = create_allele_with_annotation_tuple(session, {
            'frequencies': {
                'ExAC': {
                    'freq': {
                        'G': 0.005  # == 0.005
                    },
                    'num': {
                        'G': 9000  # Above 2000
                    }
                }
            },
            'transcripts': [
                {
                    'symbol': 'GENE1AD',
                    'transcript': 'NM_1AD.1',
                    'exon_distance': 0
                }
            ]
        })

        session.commit()

        af = AlleleFilter(session, GLOBAL_CONFIG)
        gp_key = ('testpanel', 'v01')
        # allele_ids = [pa1ad.id, pa1ar.id, pa1nogene.id, pa2.id, pa3.id, pa4.id]
        allele_info = {pa1ad.id: (pa1ad, pa1adanno),
                       pa1ar.id: (pa1ar, pa1aranno),
                       pa1nogene.id: (pa1nogene, pa1nogeneanno),
                       pa2.id: (pa2, pa2anno),
                       pa3.id: (pa3, pa3anno),
                       pa4.id: (pa4, pa4anno)}

        result = af.filter_alleles({gp_key: allele_info.keys()})

        assert set(result[gp_key]['excluded_allele_ids']['frequency']) == set(allele_info.keys()),\
            create_error_message(allele_info.keys() + result[gp_key]['excluded_allele_ids']['frequency'], allele_info)

        ##
        # Test negative cases
        ##

        # Test external
        # GENE1AD: external: 0.005/0.001 , internal: 0.05/0.01
        na1ad = create_allele_with_annotation(session, {
            'frequencies': {
                'ExAC': {
                    'freq': {
                        'G': 0.0049   # Below 0.005
                    },
                    'num': {
                        'G': 9000  # Above 2000
                    }
                }
            },
            'transcripts': [
                {
                    'symbol': 'GENE1AD',
                    'transcript': 'NM_1AD.1',
                    'exon_distance': 0
                }
            ]
        })

        # GENE1AR: external: 0.30/0.1 , internal: 0.05/0.01
        na1ar = create_allele_with_annotation(session, {
            'frequencies': {
                'ExAC': {
                    'freq': {
                        'G': 0.2999   # Below 0.3
                    },
                    'num': {
                        'G': 9000  # Above 2000
                    }
                }
            },
            'transcripts': [
                {
                    'symbol': 'GENE1AR',
                    'transcript': 'NM_1AR.1',
                    'exon_distance': 0
                }
            ]
        })

        # Test internal
        # GENE2: external: 0.5/0.1 , internal: 0.7/0.6
        na2 = create_allele_with_annotation(session, {
            'frequencies': {
                'inDB': {
                    'freq': {
                        'AF': 0.69  # Below 0.7
                    }
                }
            },
            'transcripts': [
                {
                    'symbol': 'GENE2',
                    'transcript': 'NM_2.1',
                    'exon_distance': 0
                }
            ]
        })

        # Test missing frequency
        # GENE1: external: 0.005/0.001 , internal: 0.05/0.01
        na3 = create_allele_with_annotation(session, {
            'frequencies': {},
            'transcripts': [
                {
                    'symbol': 'GENE1AD',
                    'transcript': 'NM_1AD.1',
                    'exon_distance': 0
                }
            ]
        })

        # Test 0 frequency
        # GENE1: external: 0.005/0.001 , internal: 0.05/0.01
        na4 = create_allele_with_annotation(session, {
            'frequencies': {
                'ExAC': {
                    'freq': {
                        'G': 0
                    },
                    'num': {
                        'G': 9000  # Above 2000
                    }
                }
            },
            'transcripts': [
                {
                    'symbol': 'GENE1AD',
                    'transcript': 'NM_1AD.1',
                    'exon_distance': 0
                }
            ]
        })

        session.commit()

        af = AlleleFilter(session, GLOBAL_CONFIG)
        gp_key = ('testpanel', 'v01')
        allele_ids = [na1ad.id, na1ar.id, na2.id, na3.id, na4.id]
        result = af.filter_alleles({gp_key: allele_ids})

        assert set(result[gp_key]['allele_ids']) == set(allele_ids)

    @pytest.mark.aa(order=3)
    def test_intronic_filtering(self, session):

        # intronic_region [-10, 5]

        ##
        # Test positive cases
        ##

        pa1 = create_allele_with_annotation(session, {
            'transcripts': [
                {
                    'transcript': 'NM_1AD.1',
                    'exon_distance': -11
                }
            ]
        })

        pa2 = create_allele_with_annotation(session, {
            'transcripts': [
                {
                    'transcript': 'NM_2.1',
                    'exon_distance': 6
                }
            ]
        })

        pa3 = create_allele_with_annotation(session, {
            'transcripts': [
                {
                    'transcript': 'NM_1AD.1',
                    'exon_distance': 10000000
                }
            ]
        })

        pa4 = create_allele_with_annotation(session, {
            'transcripts': [
                {
                    'transcript': 'NM_1AD.1',
                    'exon_distance': -1000000
                }
            ]
        })

        pa5 = create_allele_with_annotation(session, {
            'transcripts': [
                {
                    'transcript': 'NM_1AD.1',
                    'exon_distance': -1000000
                },
                {
                    'transcript': 'SOME_OTHER_TRANSCRIPT_NOT_FOR_FILTERING',
                    'exon_distance': 0
                }
            ]
        })


        session.commit()

        af = AlleleFilter(session, GLOBAL_CONFIG)
        gp_key = ('testpanel', 'v01')
        allele_ids = [pa1.id, pa2.id, pa3.id, pa4.id, pa5.id]
        result = af.filter_alleles({gp_key: allele_ids})

        assert set(result[gp_key]['excluded_allele_ids']['intronic']) == set(allele_ids)

        ##
        # Test negative cases
        ##

        na1 = create_allele_with_annotation(session, {
            'transcripts': [
                {
                    'transcript': 'NM_1AD.1',
                    'exon_distance': -10
                }
            ]
        })

        na2 = create_allele_with_annotation(session, {
            'transcripts': [
                {
                    'transcript': 'NM_2.1',
                    'exon_distance': 5
                }
            ]
        })

        na3 = create_allele_with_annotation(session, {
            'transcripts': [
                {
                    'transcript': 'NM_1AD.1',
                    'exon_distance': 0
                }
            ]
        })

        na4 = create_allele_with_annotation(session, {
            'transcripts': [
                {
                    'transcript': 'NM_1AD.1',
                    'exon_distance': 0
                }
            ]
        })

        # Check that annotation transcripts are filtered properly on genepanel transcripts
        na5 = create_allele_with_annotation(session, {
            'transcripts': [
                {
                    'transcript': 'NM_1AD.1',
                    'exon_distance': -1
                },
                {
                    'transcript': 'NOT_IN_GENEPANEL',
                    'exon_distance': 1000
                }
            ]
        })

        # Test that annotation transcripts matching config include_regex are included in filter
        na6 = create_allele_with_annotation(session, {
            'transcripts': [
                {
                    'transcript': 'NM_1AD.1',
                    'exon_distance': -1000
                },
                {
                    'transcript': 'NM_SOME_OTHER_TRANSCRIPT_NOT_IN_GENEPANEL',  # Should filter on NM_.*
                    'exon_distance': None
                }
            ]
        })

        # Test one transcript inside and one outside exonic region, should not be filtered out
        na7 = create_allele_with_annotation(session, {
            'transcripts': [
                {
                    'transcript': 'NM_1AD.1',
                    'exon_distance': -100
                },
                {
                    'transcript': 'NM_SOME_OTHER_TRANSCRIPT',  # Is checked due to inclusion_regex
                    'exon_distance': -1
                }
            ]
        })

        session.commit()

        af = AlleleFilter(session, GLOBAL_CONFIG)
        gp_key = ('testpanel', 'v01')
        allele_ids = [na1.id, na2.id, na3.id, na4.id, na5.id, na6.id, na7.id]
        result = af.filter_alleles({gp_key: allele_ids})

        assert set(result[gp_key]['allele_ids']) == set(allele_ids)

    @pytest.mark.aa(order=4)
    def test_utr_filtering(self, session):
        ##
        # Test positive case
        ##

        pa1 = create_allele_with_annotation(session, {
            'transcripts': [
                {
                    'symbol': 'GENE1AD',
                    'transcript': 'NM_1AD.1',
                    'consequences': ['3_prime_UTR_variant']
                }
            ]
        })

        pa2 = create_allele_with_annotation(session, {
            'transcripts': [
                {
                    'symbol': 'GENE1AD',
                    'transcript': 'NM_1AD.1',
                    'consequences': ['3_prime_UTR_variant', 'non_coding_transcript_exon_variant']
                }
            ]
        })

        pa3 = create_allele_with_annotation(session, {
            'transcripts': [
                {
                    'symbol': 'GENE1AD',
                    'transcript': 'NM_1AD.1',
                    'consequences': ['non_coding_transcript_exon_variant']
                },
                {
                    'symbol': 'GENE2',
                    'transcript': 'NM_2.1',
                    'consequences': ['5_prime_UTR_variant', 'intron_variant']
                }
            ]
        })

        session.commit()

        af = AlleleFilter(session, GLOBAL_CONFIG)
        gp_key = ('testpanel', 'v01')
        allele_ids = [pa1.id, pa2.id, pa3.id]
        result = af.filter_alleles({gp_key: allele_ids})

        assert set(result[gp_key]['excluded_allele_ids']['utr']) == set(allele_ids)

        ##
        # Test negative cases
        ##

        na1 = create_allele_with_annotation(session, {
            'transcripts': [
                {
                    'symbol': 'GENE1AD',
                    'transcript': 'NM_1AD.1',
                }
            ]
        })

        na2 = create_allele_with_annotation(session, {
            'transcripts': [
                {
                    'symbol': 'GENE1AD',
                    'transcript': 'NM_1AD.1',
                    'consequences': ['splice_region_variant']
                },
            ]
        })

        na3 = create_allele_with_annotation(session, {
            'transcripts': [
                {
                    'symbol': 'GENE1AD',
                    'transcript': 'NM_1AD.1',
                    'consequences': ['SOME_DUMMY_CONSEQUENCE_NOT_DEFINED']
                },
            ]
        })

        na4 = create_allele_with_annotation(session, {
            'transcripts': [
                {
                    'symbol': 'GENE1AD',
                    'transcript': 'NM_1AD.1',
                    'consequences': ['5_prime_UTR_variant', 'splice_region_variant']
                },
            ]
        })

        na5 = create_allele_with_annotation(session, {
            'transcripts': [
                {
                    'symbol': 'GENE1AD',
                    'transcript': 'NM_1AD.1',
                    'consequences': ['5_prime_UTR_variant']
                },
                {
                    'symbol': 'GENE2',
                    'transcript': 'NM_2.1',
                    'consequences': ['splice_region_variant']
                }
            ]
        })

        session.commit()

        af = AlleleFilter(session, GLOBAL_CONFIG)
        gp_key = ('testpanel', 'v01')
        allele_ids = [na1.id, na2.id, na3.id, na4.id, na5.id]
        result = af.filter_alleles({gp_key: allele_ids})

        assert set(result[gp_key]['allele_ids']) == set(allele_ids)


    @pytest.mark.aa(order=6)
    def test_filter_order(self, session):

        # Test filter order: gene -> frequency -> intronic

        # Would be filtered on frequency, gene and intronic
        a1 = create_allele_with_annotation(session, {
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
                    'transcript': 'NM_3.1',
                    'exon_distance': 1000
                }
            ]
        })

        # Would be filtered on frequency and intronic
        a2 = create_allele_with_annotation(session, {
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
                    'transcript': 'NM_1AR.1',
                    'exon_distance': 1000
                }
            ]
        })

        # Would be filtered on intronic only
        a3 = create_allele_with_annotation(session, {
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
                    'transcript': 'NM_2.1',
                    'exon_distance': 1000
                }
            ]
        })

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

        assert a3.id in result[gp_key]['excluded_allele_ids']['intronic']
        assert a1.id in result[gp_key]['excluded_allele_ids']['intronic']
        assert a2.id not in result[gp_key]['excluded_allele_ids']['intronic']

        assert a1.id not in result[gp_key]['allele_ids']
        assert a2.id not in result[gp_key]['allele_ids']
        assert a3.id not in result[gp_key]['allele_ids']

