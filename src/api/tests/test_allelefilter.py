"""
Integration/unit test for the AlleleFilter module.
Since it consists mostly of database queries, it's tested on a live database.
"""
import copy
import pytest

from api.util.allelefilter import AlleleFilter
from vardb.datamodel import allele, annotation, gene, annotationshadow

# prevent screen getting filled with output (useful when testing manually)
#import logging
#logging.getLogger('vardb.deposit.deposit_genepanel').setLevel(logging.CRITICAL)


GLOBAL_CONFIG = {
    'variant_criteria': {
        "intronic_region": [-10, 5],
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


def global_with_overridden_threshold(initial, override):
    return copy.deepcopy(initial).update(override)


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

    g1_ad = gene.Gene(hgnc_id=1e6, hgnc_symbol="GENE1AD")
    g1_ar = gene.Gene(hgnc_id=2e6, hgnc_symbol="GENE1AR")
    g2 = gene.Gene(hgnc_id=3e6, hgnc_symbol="GENE2")
    g3 = gene.Gene(hgnc_id=4e6, hgnc_symbol="GENE3")
    g4 = gene.Gene(hgnc_id=5e6, hgnc_symbol="GENE4")
    g5 = gene.Gene(hgnc_id=6e6, hgnc_symbol="GENE5")

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
        a1ad, _ = create_allele_with_annotation(session,
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
                        'transcript': 'NM_1AD.1',
                        'exon_distance': 0
                    }
                ]
            }
        )

        # Test less_common

        # GENE1AR: external: 0.30/0.1 , internal: 0.05/0.01
        a1ar, _ = create_allele_with_annotation(session,
            {
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
            }
        )

        # DOESNT_EXIST: should give 'default' group, since no connected 'AR' phenotype
        # external: 0.30/0.1 , internal: 0.05/0.01
        a1nogene, _ = create_allele_with_annotation(session,
            {
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
            }
        )

        # Test null_freq

        a1nofreq, _  = create_allele_with_annotation(session,
            {
                'frequencies': {},
                'transcripts': [
                    {
                        'symbol': 'DOESNT_EXIST',
                        'transcript': 'DOESNT_EXIST',
                        'exon_distance': 0
                    }
                ]
            }
        )

        # Test gene specific thresholds
        a1g2, _ = create_allele_with_annotation(session,
            {
                'frequencies': {
                    'ExAC': {
                        'freq': {
                            'G': 0.3  # Less than 0.5, greater than 0.1
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
                        'exon_distance': 0
                    }
                ]
            }
        )

        # Test gene specific thresholds with multiple genes
        # Should hit low_freq based on GENE2 thresholds
        a1adg2, _ = create_allele_with_annotation(session,
            {
                'frequencies': {
                    'ExAC': {
                        'freq': {
                            'G': 0.006  # Less than GENE2 0.1, greater than AD default 0.005
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
                        'exon_distance': 0
                    },
                    {
                        'symbol': 'GENE1AD',
                        'transcript': 'NM_1AD.1',
                        'exon_distance': 0
                    }
                ]
            }
        )

        # FIXME: This should be fixed by applying the highest thresholds for the genes available. Currently only using the gene override thresholds.
        # # Should ideally be low_freq
        # # GENE4 common for frequencies above 1e-12
        # # AD low freq for frequencies below 0.005
        # a1adg4 = create_allele_with_annotation(session, {
        #     'frequencies': {
        #         'ExAC': {
        #             'freq': {
        #                 'G': 0.00001  # Greater than GENE4 1e-12, less than AD default 0.005
        #             },
        #             'num': {
        #                 'G': 9000  # Above 2000
        #             }
        #         }
        #     },
        #     'transcripts': [
        #         {
        #             'symbol': 'GENE4',
        #             'transcript': 'NM_4.1',
        #             'exon_distance': 0
        #         },
        #         {
        #             'symbol': 'GENE1AD',
        #             'transcript': 'NM_1AD.1',
        #             'exon_distance': 0
        #         }
        #     ]
        # })

        session.commit()

        af = AlleleFilter(session, GLOBAL_CONFIG)
        gp_key = ('testpanel', 'v01')
        allele_info = [a1ad.id, a1ar.id, a1nogene.id, a1nofreq.id, a1g2.id, a1adg2.id]
        result = af.get_commonness_groups({gp_key: allele_info})

        assert set(result[gp_key]['common']) == set([a1ad.id])
        assert set(result[gp_key]['less_common']) == set([a1ar.id, a1g2.id])
        assert set(result[gp_key]['low_freq']) == set([a1nogene.id, a1adg2.id])
        assert set(result[gp_key]['null_freq']) == set([a1nofreq.id])

        ##
        # Test num thresholds
        ##

        # Test below threshold, one source
        anum1, anum1anno = create_allele_with_annotation(session, {
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
        anum2, anum2anno = create_allele_with_annotation(session, {
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
        anum3, anum3anno = create_allele_with_annotation(session, {
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
        anum4, anum4anno = create_allele_with_annotation(session, {
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
        a2common, _ = create_allele_with_annotation(session,
            {
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
            }
        )

        session.commit()
        gp_key = ('testpanel', 'v01')
        allele_info = [a2common.id]
        result = af.get_commonness_groups({gp_key: allele_info})

        assert result[gp_key]['common'] == set([a2common.id])
        assert not result[gp_key]['less_common']
        assert not result[gp_key]['low_freq']
        assert not result[gp_key]['null_freq']

        a2less_common, _ = create_allele_with_annotation(session,
            {
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
            }
        )

        session.commit()
        gp_key = ('testpanel', 'v01')
        allele_info = [a2less_common.id]
        result = af.get_commonness_groups({gp_key: allele_info})

        assert not result[gp_key]['common']
        assert result[gp_key]['less_common'] == set([a2less_common.id])
        assert not result[gp_key]['low_freq']
        assert not result[gp_key]['null_freq']

        a2low_freq, _ = create_allele_with_annotation(session,
            {
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
            }
        )

        session.commit()
        gp_key = ('testpanel', 'v01')
        allele_info = [a2low_freq.id]
        result = af.get_commonness_groups({gp_key: allele_info})

        assert not (result[gp_key]['common'])
        assert not result[gp_key]['less_common']
        assert result[gp_key]['low_freq'] == set([a2low_freq.id])
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
        pa1ad, pa1adanno = create_allele_with_annotation(session,
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
                        'transcript': 'NM_1AD.1',
                        'exon_distance': 0
                    }
                ]
            }
        )

        # GENE1AR: external: 0.30/0.1 , internal: 0.05/0.01
        pa1ar, pa1aranno = create_allele_with_annotation(session,
            {
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
            }
        )


        # DOESNT_EXIST: should give 'default' group, since no connected 'AR' phenotype
        # external: 0.30/0.1 , internal: 0.05/0.01
        pa1nogene, pa1nogeneanno = create_allele_with_annotation(session,
            {
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
                ],

            }
        )


        # Test internal
        # GENE2: external: 0.5/0.1 , internal: 0.7/0.6
        pa2, pa2anno = create_allele_with_annotation(session,
            {
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
                ],
            }
        )

        # Test conflicting external/internal
        # GENE1AD: external: 0.005/0.001 , internal: 0.05/0.01
        pa3, pa3anno  = create_allele_with_annotation(session,
            {
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
            }
        )

        # Test right on threshold
        # GENE1AD: external: 0.005/0.001 , internal: 0.05/0.01
        pa4, pa4anno = create_allele_with_annotation(session,
            {
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
            }
        )

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
        na1ad, _ = create_allele_with_annotation(session,
            {
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
            }
        )

        # GENE1AR: external: 0.30/0.1 , internal: 0.05/0.01
        na1ar, _ = create_allele_with_annotation(session,
            {
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
            }
        )

        # Test internal
        # GENE2: external: 0.5/0.1 , internal: 0.7/0.6
        na2, _ = create_allele_with_annotation(session,
            {
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
                ],
            },
            allele_data={
                    "chromosome": "2",
                    "start_position": 2300,
                    "open_end_position": 2301,
                    "change_from": "A",
                    "change_to": "T",
                    "change_type": "SNP",
                    "vcf_pos": 2301,
                    "vcf_ref": "A",
                    "vcf_alt": "T"
            }
        )

        # Test missing frequency
        # GENE1: external: 0.005/0.001 , internal: 0.05/0.01
        na3, _ = create_allele_with_annotation(session,
            {
                'frequencies': {},
                'transcripts': [
                    {
                        'symbol': 'GENE1AD',
                        'transcript': 'NM_1AD.1',
                        'exon_distance': 0
                    }
                ]
            }
        )

        # Test 0 frequency
        # GENE1: external: 0.005/0.001 , internal: 0.05/0.01
        na4, _ = create_allele_with_annotation(session,
            {
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
            }
        )

        session.commit()

        af = AlleleFilter(session, GLOBAL_CONFIG)
        gp_key = ('testpanel', 'v01')
        allele_ids = [na1ad.id, na1ar.id, na2.id, na3.id, na4.id]
        result = af.filter_alleles({gp_key: allele_ids})

        assert set(result[gp_key]['allele_ids']) == set(allele_ids)

    @pytest.mark.aa(order=3)
    def test_genomic_region_filtering(self, session):
        # intronic_region [-10, 5]
        # coding_region [-20, 20]
        # t1:
        # tx_start=1000,
        # tx_end=1500,
        # strand='+',
        # cds_start=1230,
        # cds_end=1430,
        # exon_starts=[1100, 1200, 1300, 1400],
        # exon_ends=[1160, 1260, 1360, 1460]

        # Outside all genepanel transcripts
        pa1, _ = create_allele_with_annotation(session,
            None,
            {
                "chromosome": "1",
                "start_position": 1600,
                "open_end_position": 1601,
            }
        )

        # Within transcript, but outside coding region
        pa2, _ = create_allele_with_annotation(session,
            None,
            {
                "chromosome": "1",
                "start_position": 1100,
                "open_end_position": 1101,
            }
        )

        # Within transcript, but outside coding region
        pa3, _ = create_allele_with_annotation(session,
            None,
            {
                "chromosome": "1",
                "start_position": 1451,
                "open_end_position": 1452,
            }
        )

        # Intronic variant (-11)
        pa4, _ = create_allele_with_annotation(session,
            None,
            {
                "chromosome": "1",
                "start_position": 1289,
                "open_end_position": 1290,
            }
        )

        # Intronic variant (+6) (in UTR)
        pa5, _ = create_allele_with_annotation(session,
            None,
            {
                "chromosome": "1",
                "start_position": 1466,
                "open_end_position": 1467,
            }
        )

        # Intronic variant (+6)
        pa6, _ = create_allele_with_annotation(session,
            None,
            {
                "chromosome": "1",
                "start_position": 1266,
                "open_end_position": 1267,
            }
        )

        # t5:
        # chromosome='5',
        # tx_start=5000,
        # tx_end=5500,
        # strand='-',
        # cds_start=5230,
        # cds_end=5430,
        # exon_starts=[5100, 5200, 5300, 5400],
        # exon_ends=[5160, 5260, 5360, 5460]

        # UTR variant [+21] on reverse transcript
        pa7, _ = create_allele_with_annotation(session,
            None,
            {
                "chromosome": "5",
                "start_position": 5209,
                "open_end_position": 5210,
            }
        )

        # UTR variant (-13) on reverse transcript
        pa8, _ = create_allele_with_annotation(session,
            None,
            {
                "chromosome": "5",
                "start_position": 5443,
                "open_end_position": 5444,
            }
        )

        # Intronic variant (+6) on reverse transcript
        pa9, _ = create_allele_with_annotation(session,
            None,
            {
                "chromosome": "5",
                "start_position": 5294,
                "open_end_position": 5295,
            }
        )

        # Intronic variant (-11) on reverse transcript
        pa10, _ = create_allele_with_annotation(session,
            None,
            {
                "chromosome": "5",
                "start_position": 5271,
                "open_end_position": 5272,
            }
        )


        session.commit()

        af = AlleleFilter(session, GLOBAL_CONFIG)
        gp_key = ('testpanel', 'v01')
        allele_ids = [pa1.id, pa2.id, pa3.id, pa4.id, pa5.id, pa6.id, pa7.id, pa8.id, pa9.id, pa10.id]

        result = af.filter_alleles({gp_key: allele_ids})

        assert set(result[gp_key]['excluded_allele_ids']['region']) == set(allele_ids)


        # Test negative cases
        # t1:
        # tx_start=1000,
        # tx_end=1500,
        # strand='+',
        # cds_start=1230,
        # cds_end=1430,
        # exon_starts=[1100, 1200, 1300, 1400],
        # exon_ends=[1160, 1260, 1360, 1460]

        # Within coding exon
        na1, _ = create_allele_with_annotation(session,
            None,
            {
                "chromosome": "1",
                "start_position": 1300,
                "open_end_position": 1301,
            }
        )

        # Within splice region [-10]
        na2, _ = create_allele_with_annotation(session,
            None,
            {
                "chromosome": "1",
                "start_position": 1290,
                "open_end_position": 1291,
            }
        )


        # Within splice region of UTR exon [-10]
        na3, _ = create_allele_with_annotation(session,
            None,
            {
                "chromosome": "1",
                "start_position": 1090,
                "open_end_position": 1091,
            }
        )

        # Within splice region of UTR exon [+5]
        na4, _ = create_allele_with_annotation(session,
            None,
            {
                "chromosome": "1",
                "start_position": 1165,
                "open_end_position": 1166,
            }
        )

        # Within utr region [20]
        na5, _ = create_allele_with_annotation(session,
            None,
            {
                "chromosome": "1",
                "start_position": 1450,
                "open_end_position": 1451,
            }
        )

        # Within utr region [-12]
        na6, _ = create_allele_with_annotation(session,
            None,
            {
                "chromosome": "1",
                "start_position": 1218,
                "open_end_position": 1219,
            }
        )

        # t5:
        # chromosome='5',
        # tx_start=5000,
        # tx_end=5500,
        # strand='-',
        # cds_start=5230,
        # cds_end=5430,
        # exon_starts=[5100, 5200, 5300, 5400],
        # exon_ends=[5160, 5260, 5360, 5460]

        # Within utr region [-12] on reverse transcript
        na7, _ = create_allele_with_annotation(session,
            None,
            {
                "chromosome": "5",
                "start_position": 5442,
                "open_end_position": 5443,
            }
        )

        # Within utr region [20] on reverse transcript
        na8, _ = create_allele_with_annotation(session,
            None,
            {
                "chromosome": "5",
                "start_position": 5210,
                "open_end_position": 5211,
            }
        )

        # Within exonic region [-10] on reverse transcript
        na9, _ = create_allele_with_annotation(session,
            None,
            {
                "chromosome": "5",
                "start_position": 5470,
                "open_end_position": 5471,
            }
        )

        # Within exonic region [+5] on reverse transcript
        na10, _ = create_allele_with_annotation(session,
            None,
            {
                "chromosome": "5",
                "start_position": 5095,
                "open_end_position": 5096,
            }
        )


        session.commit()

        af = AlleleFilter(session, GLOBAL_CONFIG)
        gp_key = ('testpanel', 'v01')
        allele_ids = [na1.id, na2.id, na3.id, na4.id, na5.id, na6.id, na7.id, na8.id, na9.id, na10.id]
        result = af.filter_alleles({gp_key: allele_ids})

        assert set(result[gp_key]['allele_ids']) == set(allele_ids)


    @pytest.mark.aa(order=4)
    def test_hgvsc_region_filtering(self, session):
        """
        All variants are outside any transcripts (in genomic position), but are annotated with a genepanel transcript
        with exon_distance or coding_region_distance within intronic_region/utr_region
        """
        # Should be saved as annotated with exon_distance -10
        a1, _ = create_allele_with_annotation(session,
            {
                'transcripts': [
                    {
                        'symbol': 'GENE1',
                        'transcript': 'NM_1AD.1',
                        'exon_distance': -10,
                        'coding_region_distance': None,
                    }
                ],
            },
            {
                "chromosome": "HGSVC",
            }
        )

        # Should be saved as annotated with exon_distance +5
        a2, _ = create_allele_with_annotation(session,
            {
                'transcripts': [
                    {
                        'symbol': 'GENE1',
                        'transcript': 'NM_1AD.1',
                        'exon_distance': 5,
                        'coding_region_distance': None,
                    }
                ],
            },
            {
                "chromosome": "HGSVC",
            }
        )

        # Should be saved as annotated with coding_region_distance -12
        a3, _ = create_allele_with_annotation(session,
            {
                'transcripts': [
                    {
                        'symbol': 'GENE1',
                        'transcript': 'NM_1AD.1',
                        'exon_distance': 0,
                        'coding_region_distance': -12,
                    }
                ],
            },
            {
                "chromosome": "HGSVC",
            }
        )

        # Should be saved as annotated with coding_region_distance +20
        a4, _ = create_allele_with_annotation(session,
            {
                'transcripts': [
                    {
                        'symbol': 'GENE1',
                        'transcript': 'NM_1AD.1',
                        'exon_distance': 0,
                        'coding_region_distance': 20,
                    }
                ],
            },
            {
                "chromosome": "HGSVC",
            }
        )

        na1, _ = create_allele_with_annotation(session,
            {
                'transcripts': [
                    {
                        'symbol': 'GENE1',
                        'transcript': 'TRANSCRIPT_NOT_FOR_FILTERING',
                        'exon_distance': 0,
                        'coding_region_distance': 0,
                    }
                ],
            },
            {
                "chromosome": "HGSVC",
            }
        )

        session.commit()


        gp_key = ('testpanel', 'v01')
        allele_ids = [a1.id, a2.id, a3.id, a4.id, na1.id]

        # Run first with no padding, to make sure that all are filtered out
        config_no_padding = copy.deepcopy(GLOBAL_CONFIG)
        config_no_padding['variant_criteria']['intronic_region'] = [0,0]
        config_no_padding['variant_criteria']['utr_region'] = [0,0]

        af = AlleleFilter(session, config_no_padding)

        result = af.filter_alleles({gp_key: allele_ids})
        assert set(result[gp_key]['excluded_allele_ids']['region']) == set(allele_ids)

        # Apply the global config, to ensure that these are captured by the computed distance
        af = AlleleFilter(session, GLOBAL_CONFIG)

        result = af.filter_alleles({gp_key: allele_ids})

        assert set(result[gp_key]['allele_ids']) == set(allele_ids)-set([na1.id])
        assert set(result[gp_key]['excluded_allele_ids']['region']) == set([na1.id])


    @pytest.mark.aa(order=5)
    def test_consequence_filtering(self, session):
        pa1, _ = create_allele_with_annotation(session,
            {
                'transcripts': [
                    {
                        'symbol': 'DOES_NOT_EXIST',
                        'transcript': 'NM_DOES_NOT_EXIST',
                        'consequences': ['intron_variant']
                    }
                ],
            },
            {
                "chromosome": "CSQ",
            }
        )


        pa2, _ = create_allele_with_annotation(session,
            {
                'transcripts': [
                    {
                        'symbol': 'GENE1',
                        'transcript': 'NM_1AD.1',
                        'consequences': ['intron_variant']
                    }
                ],
            },
            {
                "chromosome": "CSQ",
            }
        )


        pa3, _ = create_allele_with_annotation(session,
            {
                'transcripts': [
                    {
                        'symbol': 'GENE1',
                        'transcript': 'NM_1AD.1',
                        'consequences': ['intron_variant']
                    },
                    {
                        'symbol': 'GENE1',
                        'transcript': 'NM_1AD.1',
                        'consequences': ['downstream_gene_variant']
                    }
                ],
            },
            {
                "chromosome": "CSQ",
            }
        )


        session.commit()

        af = AlleleFilter(session, GLOBAL_CONFIG)
        gp_key = ('testpanel', 'v01')
        allele_ids = [pa1.id, pa2.id, pa3.id]
        result = af.filter_alleles({gp_key: allele_ids})

        assert set(result[gp_key]['excluded_allele_ids']['region']) == set(allele_ids)

        # Should be saved as annotated with exon_distance -10
        na1, _ = create_allele_with_annotation(session,
            {
                'transcripts': [
                    {
                        'symbol': 'DOES_NOT_EXIST',
                        'transcript': 'NM_DOES_NOT_EXIST',
                        'consequences': ['splice_region_variant']
                    }
                ],
            },
            {
                "chromosome": "CSQ",
            }
        )

        # Should be saved as annotated with exon_distance +5
        na2, _ = create_allele_with_annotation(session,
            {
                'transcripts': [
                    {
                        'symbol': 'GENE1',
                        'transcript': 'NM_1AD.1',
                        'consequences': ['intron_variant','splice_region_variant']
                    }
                ],
            },
            {
                "chromosome": "CSQ",
            }
        )

        # Should be saved as annotated with coding_region_distance -12
        na3, _ = create_allele_with_annotation(session,
            {
                'transcripts': [
                    {
                        'symbol': 'DOES_NOT_EXIST1',
                        'transcript': 'NM_DOES_NOT_EXIST.1',
                        'consequences': ['intron_variant']
                    },
                    {
                        'symbol': 'DOES_NOT_EXIST2',
                        'transcript': 'NM_DOES_NOT_EXIST2.1',
                        'consequences': ['missense_variant']
                    }
                ],
            },
            {
                "chromosome": "CSQ",
            }
        )

        # Should be saved as annotated with coding_region_distance +20
        na4, _ = create_allele_with_annotation(session,
            {
                'transcripts': [
                    {
                        'symbol': 'GENE1',
                        'transcript': 'NM_1AD.1',
                        'exon_distance': 0,
                        'coding_region_distance': 20,
                    }
                ],
            },
            {
                "chromosome": "CSQ",
            }
        )

        session.commit()

        af = AlleleFilter(session, GLOBAL_CONFIG)
        gp_key = ('testpanel', 'v01')
        allele_ids = [na1.id, na2.id, na3.id, na4.id]
        result = af.filter_alleles({gp_key: allele_ids})

        assert set(result[gp_key]['allele_ids']) == set(allele_ids)


    @pytest.mark.aa(order=6)
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

