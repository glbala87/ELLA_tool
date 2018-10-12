"""
Integration/unit test for the AlleleFilter module.
Since it consists mostly of database queries, it's tested on a live database.
"""
import copy
import pytest

from api.allelefilter.frequencyfilter import FrequencyFilter
from vardb.datamodel import allele, annotation, gene, annotationshadow, assessment


# prevent screen getting filled with output (useful when testing manually)
#import logging
#logging.getLogger('vardb.deposit.deposit_genepanel').setLevel(logging.CRITICAL)


GLOBAL_CONFIG = {
    'filter': {
        "frequency_groups": {
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

COMMONESS_FILTER_CONFIG = {
    'thresholds': {
        'AD': {
            "external": {
                "hi_freq_cutoff": 0.005,
                "lo_freq_cutoff": 0.001
            },
            "internal": {
                "hi_freq_cutoff": 0.05,
                "lo_freq_cutoff": 0.01
            }
        },
        'default': {
            "external": {
                "hi_freq_cutoff": 0.3,
                "lo_freq_cutoff": 0.1
            },
            "internal": {
                "hi_freq_cutoff": 0.05,
                "lo_freq_cutoff": 0.01
            }
        }
    },
    'num_thresholds': {
        "ExAC": {
            "G": 2000,
            "FIN": 2000,
        }
    },
    'genes': {
        1234: {
            'thresholds': {
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

FILTER_ALLLES_FILTER_CONFIG = {
    'thresholds': {
        'AD': {
            "external": 0.005,
            "internal": 0.05
        },
        'default': {
            "external": 0.3,
            "internal": 0.05,
        }
    },
    'num_thresholds': {
        "ExAC": {
            "G": 2000,
            "FIN": 2000,
        }
    },
    'genes': {
        1234: {
            'thresholds': {
                "external":  0.5,
                "internal":  0.7
            }
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

    genepanel.transcripts = [t1_ad, t1_ar, t2]
    genepanel.phenotypes = [p1, p2]
    return genepanel


class TestFrequencyFilter(object):

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
                        'hgnc_id': 1,
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
                        'hgnc_id': 2,
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
                        'hgnc_id': 100,
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
                        'hgnc_id': 100,
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
                        'hgnc_id': 1234,
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
                        'hgnc_id': 1234,
                        'transcript': 'NM_2.1',
                        'exon_distance': 0
                    },
                    {
                        'symbol': 'GENE1AD',
                        'hgnc_id': 1,
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
        #             'hgnc_id': 1,
        #             'transcript': 'NM_1AD.1',
        #             'exon_distance': 0
        #         }
        #     ]
        # })

        session.commit()

        ff = FrequencyFilter(session, GLOBAL_CONFIG)
        gp_key = ('testpanel', 'v01')
        allele_info = [a1ad.id, a1ar.id, a1nogene.id, a1nofreq.id, a1g2.id, a1adg2.id]
        result = ff.get_commonness_groups({gp_key: allele_info}, COMMONESS_FILTER_CONFIG)

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
                    'hgnc_id': 1,
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
                    'hgnc_id': 1,
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
                    'hgnc_id': 1,
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
                    'hgnc_id': 1234,
                    'transcript': 'NM_2.1',
                    'exon_distance': 0
                }
            ]
        })

        session.commit()

        ff = FrequencyFilter(session, GLOBAL_CONFIG)
        gp_key = ('testpanel', 'v01')
        allele_info = {anum1.id: (anum1, anum1anno),
                       anum2.id: (anum2, anum2anno),
                       anum3.id: (anum3, anum3anno),
                       anum4.id: (anum4, anum4anno)}
        result = ff.get_commonness_groups({gp_key: allele_info.keys()}, COMMONESS_FILTER_CONFIG)

        assert set(result[gp_key]['num_threshold']) == set([anum1.id])

        assert set(result[gp_key]['common']) == set([anum2.id, anum3.id, anum4.id])

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
                        'hgnc_id': 1,
                        'transcript': 'NM_1AD.1',
                        'exon_distance': 0
                    }
                ]
            }
        )

        session.commit()
        gp_key = ('testpanel', 'v01')
        allele_info = [a2common.id]
        result = ff.get_commonness_groups({gp_key: allele_info}, COMMONESS_FILTER_CONFIG)

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
                        'hgnc_id': 1,
                        'transcript': 'NM_1AD.1',
                        'exon_distance': 0
                    }
                ]
            }
        )

        session.commit()
        gp_key = ('testpanel', 'v01')
        allele_info = [a2less_common.id]
        result = ff.get_commonness_groups({gp_key: allele_info}, COMMONESS_FILTER_CONFIG)

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
                        'hgnc_id': 1,
                        'transcript': 'NM_1AD.1',
                        'exon_distance': 0
                    }
                ]
            }
        )

        session.commit()
        gp_key = ('testpanel', 'v01')
        allele_info = [a2low_freq.id]
        result = ff.get_commonness_groups({gp_key: allele_info}, COMMONESS_FILTER_CONFIG)

        assert not (result[gp_key]['common'])
        assert not result[gp_key]['less_common']
        assert result[gp_key]['low_freq'] == set([a2low_freq.id])
        assert not result[gp_key]['null_freq']

    @pytest.mark.aa(order=2)
    def test_frequency_filtering(self, session):

        # Filter config should end up being the following
        # GENE1AD: external: 0.005/0.001 , internal: 0.05/0.01
        # GENE1AR: external: 0.30/0.01 , internal: 0.05/0.01
        # GENE2: external: 0.5/0.1 , internal: 0.7/0.6


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
                        'hgnc_id': 1,
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
                        'hgnc_id': 1234,
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
                        'hgnc_id': 1,
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
                        'hgnc_id': 1,
                        'transcript': 'NM_1AD.1',
                        'exon_distance': 0
                    }
                ]
            }
        )

        session.commit()

        ff = FrequencyFilter(session, GLOBAL_CONFIG)
        gp_key = ('testpanel', 'v01')
        # allele_ids = [pa1ad.id, pa1ar.id, pa1nogene.id, pa2.id, pa3.id, pa4.id]
        allele_info = {pa1ad.id: (pa1ad, pa1adanno),
                       pa1ar.id: (pa1ar, pa1aranno),
                       pa1nogene.id: (pa1nogene, pa1nogeneanno),
                       pa2.id: (pa2, pa2anno),
                       pa3.id: (pa3, pa3anno),
                       pa4.id: (pa4, pa4anno)}

        result = ff.filter_alleles({gp_key: allele_info.keys()}, FILTER_ALLLES_FILTER_CONFIG)

        assert result[gp_key] == set(allele_info.keys())

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
                        'hgnc_id': 1,
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
                        'hgnc_id': 1234,
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
                        'hgnc_id': 1,
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
                        'hgnc_id': 1,
                        'transcript': 'NM_1AD.1',
                        'exon_distance': 0
                    }
                ]
            }
        )

        session.commit()

        ff = FrequencyFilter(session, GLOBAL_CONFIG)
        gp_key = ('testpanel', 'v01')
        allele_ids = [na1ad.id, na1ar.id, na2.id, na3.id, na4.id]
        result = ff.filter_alleles({gp_key: allele_ids}, FILTER_ALLLES_FILTER_CONFIG)

        assert not result[gp_key]
