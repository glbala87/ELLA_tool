"""
Integration/unit test for the AlleleFilter module.
Since it consists mostly of database queries, it's tested on a live database.
"""
import pytest

from api.util.allelefilter import AlleleFilter
from vardb.datamodel import allele, annotation, gene

# prevent screen getting filled with output (useful when testing manually)
#import logging
#logging.getLogger('vardb.deposit.deposit_genepanel').setLevel(logging.CRITICAL)


CONFIG = {
    'variant_criteria': {
        "intronic_region": [-10, 5],
        "genepanel_config": {
            "freq_cutoffs": {
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
            },
            "freq_num_thresholds": {
                "ExAC": {
                    "G": 2000,
                    "FIN": 2000,
                }
            }
        },
        "exclude_genes": ['GENE3'],
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
        'inclusion_regex': "NM_.*"
    }
}

GP_CONFIG = {
    'data': {
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
            },
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
    }
}

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


def create_allele_annotation(session, annotations):
    al = create_allele()
    an = create_annotation(annotations, allele=al)
    session.add(al)
    session.add(an)
    return al


def create_genepanel(config):
    # Create fake genepanel for testing purposes

    g1_ad = gene.Gene(hugo_symbol="GENE1AD")
    g1_ar = gene.Gene(hugo_symbol="GENE1AR")
    g2 = gene.Gene(hugo_symbol="GENE2")
    g3 = gene.Gene(hugo_symbol="GENE3")

    t1_ad = gene.Transcript(
        gene=g1_ad,
        refseq_name='NM_1AD.1',
        ensembl_id='ENST1AD',
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
        refseq_name='NM_1AR.1',
        ensembl_id='ENST1AR',
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
        refseq_name='NM_2.1',
        ensembl_id='ENST2',
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
        refseq_name='NM_3.1',
        ensembl_id='ENST3',
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
        config=GP_CONFIG
    )

    genepanel.transcripts = [t1_ad, t1_ar, t2, t3]
    genepanel.phenotypes = [p1, p2]
    return genepanel


class TestAlleleFilter(object):

    @pytest.mark.aa(order=0)
    def test_prepare_data(self, test_database, session):
        test_database.refresh()  # Reset db

        gp = create_genepanel(GP_CONFIG)
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
        a1ad = create_allele_annotation(session, {
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
        a1ar = create_allele_annotation(session, {
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
        a1nogene = create_allele_annotation(session, {
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

        a1nofreq = create_allele_annotation(session, {
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

        af = AlleleFilter(session, CONFIG)
        gp_key = ('testpanel', 'v01')
        allele_ids = [a1ad.id, a1ar.id, a1nogene.id, a1nofreq.id]
        result = af.get_commonness_groups({gp_key: allele_ids})

        assert set(result[gp_key]['common']) == set([a1ad.id])
        assert set(result[gp_key]['less_common']) == set([a1ar.id])
        assert set(result[gp_key]['low_freq']) == set([a1nogene.id])
        assert set(result[gp_key]['null_freq']) == set([a1nofreq.id])

        ##
        # Test num thresholds
        ##

        # Test below threshold, one source
        anum1 = create_allele_annotation(session, {
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
        anum2 = create_allele_annotation(session, {
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
        anum3 = create_allele_annotation(session, {
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

        # Test gene specific threshold override, above threshold
        anum4 = create_allele_annotation(session, {
            'frequencies': {
                'ExAC': {
                    'freq': {
                        'G': 0.6   # Above 0.5
                    },
                    'num': {
                        'G': 1001  # Above 1000
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

        session.commit()

        af = AlleleFilter(session, CONFIG)
        gp_key = ('testpanel', 'v01')
        allele_ids = [anum1.id, anum2.id, anum3.id, anum4.id]
        result = af.get_commonness_groups({gp_key: allele_ids})

        assert set(result[gp_key]['num_threshold']) == set([anum1.id])
        assert set(result[gp_key]['common']) == set([anum2.id, anum3.id, anum4.id])

        ##
        # Test ordering
        #
        # One allele should only appear in one group,
        # even if the different frequencies would give
        # hits in different ones
        ##
        a2common = create_allele_annotation(session, {
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
        allele_ids = [a2common.id]
        result = af.get_commonness_groups({gp_key: allele_ids})

        assert result[gp_key]['common'] == [a2common.id]
        assert not result[gp_key]['less_common']
        assert not result[gp_key]['low_freq']
        assert not result[gp_key]['null_freq']

        a2less_common = create_allele_annotation(session, {
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
        allele_ids = [a2less_common.id]
        result = af.get_commonness_groups({gp_key: allele_ids})

        assert not result[gp_key]['common']
        assert result[gp_key]['less_common'] == [a2less_common.id]
        assert not result[gp_key]['low_freq']
        assert not result[gp_key]['null_freq']

        a2low_freq = create_allele_annotation(session, {
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
        allele_ids = [a2low_freq.id]
        result = af.get_commonness_groups({gp_key: allele_ids})

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
        pa1ad = create_allele_annotation(session, {
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
        pa1ar = create_allele_annotation(session, {
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
        pa1nogene = create_allele_annotation(session, {
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
        pa2 = create_allele_annotation(session, {
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
        pa3 = create_allele_annotation(session, {
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
        pa4 = create_allele_annotation(session, {
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

        af = AlleleFilter(session, CONFIG)
        gp_key = ('testpanel', 'v01')
        allele_ids = [pa1ad.id, pa1ar.id, pa1nogene.id, pa2.id, pa3.id, pa4.id]
        result = af.filter_alleles({gp_key: allele_ids})

        assert set(result[gp_key]['excluded_allele_ids']['frequency']) == set(allele_ids)

        ##
        # Test negative cases
        ##

        # Test external
        # GENE1AD: external: 0.005/0.001 , internal: 0.05/0.01
        na1ad = create_allele_annotation(session, {
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
        na1ar = create_allele_annotation(session, {
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
        na2 = create_allele_annotation(session, {
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
        na3 = create_allele_annotation(session, {
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
        na4 = create_allele_annotation(session, {
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

        af = AlleleFilter(session, CONFIG)
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

        pa1 = create_allele_annotation(session, {
            'transcripts': [
                {
                    'symbol': 'GENE1AD',
                    'transcript': 'NM_1AD.1',
                    'exon_distance': -11
                }
            ]
        })

        pa2 = create_allele_annotation(session, {
            'transcripts': [
                {
                    'symbol': 'GENE2',
                    'transcript': 'NM_2.1',
                    'exon_distance': 6
                }
            ]
        })

        pa3 = create_allele_annotation(session, {
            'transcripts': [
                {
                    'symbol': 'GENE1AD',
                    'transcript': 'NM_1AD.1',
                    'exon_distance': 10000000
                }
            ]
        })

        pa4 = create_allele_annotation(session, {
            'transcripts': [
                {
                    'symbol': 'GENE1AD',
                    'transcript': 'NM_1AD.1',
                    'exon_distance': -1000000
                }
            ]
        })

        pa5 = create_allele_annotation(session, {
            'transcripts': [
                {
                    'symbol': 'GENE1AD',
                    'transcript': 'NM_1AD.1',
                    'exon_distance': -1000000
                },
                {
                    'symbol': 'GENE1AD',
                    'transcript': 'SOME_OTHER_TRANSCRIPT_NOT_FOR_FILTERING',
                    'exon_distance': 0
                }
            ]
        })


        session.commit()

        af = AlleleFilter(session, CONFIG)
        gp_key = ('testpanel', 'v01')
        allele_ids = [pa1.id, pa2.id, pa3.id, pa4.id, pa5.id]
        result = af.filter_alleles({gp_key: allele_ids})

        assert set(result[gp_key]['excluded_allele_ids']['intronic']) == set(allele_ids)

        ##
        # Test negative cases
        ##

        na1 = create_allele_annotation(session, {
            'transcripts': [
                {
                    'symbol': 'GENE1AD',
                    'transcript': 'NM_1AD.1',
                    'exon_distance': -10
                }
            ]
        })

        na2 = create_allele_annotation(session, {
            'transcripts': [
                {
                    'symbol': 'GENE2',
                    'transcript': 'NM_2.1',
                    'exon_distance': 5
                }
            ]
        })

        na3 = create_allele_annotation(session, {
            'transcripts': [
                {
                    'symbol': 'GENE1AD',
                    'transcript': 'NM_1AD.1',
                    'exon_distance': 0
                }
            ]
        })

        na4 = create_allele_annotation(session, {
            'transcripts': [
                {
                    'symbol': 'GENE1AD',
                    'transcript': 'NM_1AD.1',
                    'exon_distance': 0
                }
            ]
        })

        # Check that annotation transcripts are filtered properly on genepanel transcripts
        na5 = create_allele_annotation(session, {
            'transcripts': [
                {
                    'symbol': 'GENE1AD',
                    'transcript': 'NM_1AD.1',
                    'exon_distance': -1
                },
                {
                    'symbol': 'SOMEOTHERGENE',
                    'transcript': 'NOT_IN_GENEPANEL',
                    'exon_distance': 1000
                }
            ]
        })

        # Test that annotation transcripts matching config include_regex are included in filter
        na6 = create_allele_annotation(session, {
            'transcripts': [
                {
                    'symbol': 'GENE1AD',
                    'transcript': 'NM_1AD.1',
                    'exon_distance': -1000
                },
                {
                    'symbol': 'GENE1AD',
                    'transcript': 'NM_SOME_OTHER_TRANSCRIPT_NOT_IN_GENEPANEL', # Should filter on NM_.*
                    'exon_distance': None
                }
            ]
        })

        na7 = create_allele_annotation(session, {
            'transcripts': [
                {
                    'symbol': 'GENE1AD',
                    'transcript': 'NM_1AD.1',
                    'exon_distance': -100
                },
                {
                    'symbol': 'GENE1AD',
                    'transcript': 'NM_SOME_OTHER_TRANSCRIPT',
                    'exon_distance': -1
                }
            ]
        })


        session.commit()

        af = AlleleFilter(session, CONFIG)
        gp_key = ('testpanel', 'v01')
        allele_ids = [na1.id, na2.id, na3.id, na4.id, na5.id, na6.id, na7.id]
        result = af.filter_alleles({gp_key: allele_ids})

        assert set(result[gp_key]['allele_ids']) == set(allele_ids)

    @pytest.mark.aa(order=4)
    def test_gene_filtering(self, session):

        # exclude_gene ['GENE3']

        ##
        # Test positive case
        ##

        pa1 = create_allele_annotation(session, {
            'transcripts': [
                {
                    'symbol': 'GENE3',
                    'transcript': 'NM_3.1'
                }
            ]
        })

        pa2 = create_allele_annotation(session, {
            'transcripts': [
                {
                    'symbol': 'GENE1AD',
                    'transcript': 'NM_1AD.1',
                },
                {
                    'symbol': 'GENE3',
                    'transcript': 'TRANSCRIPT_NOT_IN_GENEPANEL_SHOULD_STILL_FILTER',
                }
            ]
        })

        session.commit()

        af = AlleleFilter(session, CONFIG)
        gp_key = ('testpanel', 'v01')
        allele_ids = [pa1.id, pa2.id]
        result = af.filter_alleles({gp_key: allele_ids})

        assert set(result[gp_key]['excluded_allele_ids']['gene']) == set(allele_ids)

        ##
        # Test negative cases
        ##

        na1 = create_allele_annotation(session, {
            'transcripts': [
                {
                    'symbol': 'GENE1AD',
                    'transcript': 'NM_1AD.1',
                }
            ]
        })

        na2 = create_allele_annotation(session, {
            'transcripts': [
                {
                    'symbol': 'GENE1AD',
                    'transcript': 'NM_1AD.1',
                },
                {
                    'symbol': 'GENE2',
                    'transcript': 'NM_2.1',
                }
            ]
        })

        session.commit()

        af = AlleleFilter(session, CONFIG)
        gp_key = ('testpanel', 'v01')
        allele_ids = [na1.id, na2.id]
        result = af.filter_alleles({gp_key: allele_ids})

        assert set(result[gp_key]['allele_ids']) == set(allele_ids)

    @pytest.mark.aa(order=5)
    def test_filter_order(self, session):

        # Test filter order: gene -> frequency -> intronic

        # Would be filtered on frequency, gene and intronic
        a1 = create_allele_annotation(session, {
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
        a2 = create_allele_annotation(session, {
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
        a3 = create_allele_annotation(session, {
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

        af = AlleleFilter(session, CONFIG)
        gp_key = ('testpanel', 'v01')
        allele_ids = [a1.id, a2.id, a3.id]
        result = af.filter_alleles({gp_key: allele_ids})

        assert a1.id in result[gp_key]['excluded_allele_ids']['gene']
        assert a2.id not in result[gp_key]['excluded_allele_ids']['gene']
        assert a3.id not in result[gp_key]['excluded_allele_ids']['gene']

        assert a2.id in result[gp_key]['excluded_allele_ids']['frequency']
        assert a1.id not in result[gp_key]['excluded_allele_ids']['frequency']
        assert a3.id not in result[gp_key]['excluded_allele_ids']['frequency']

        assert a3.id in result[gp_key]['excluded_allele_ids']['intronic']
        assert a1.id not in result[gp_key]['excluded_allele_ids']['intronic']
        assert a2.id not in result[gp_key]['excluded_allele_ids']['intronic']

        assert a1.id not in result[gp_key]['allele_ids']
        assert a2.id not in result[gp_key]['allele_ids']
        assert a3.id not in result[gp_key]['allele_ids']
