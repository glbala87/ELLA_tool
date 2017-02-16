"""
Integration/unit test for the AlleleFilter module.
Since it consists mostly of database queries, it's tested on a live database.
"""


import pytest

from api.util.allelefilter import AlleleFilter
from vardb.datamodel import allele, annotation, gene


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
                        "hi_freq_cutoff": 0.005,
                        "lo_freq_cutoff": 0.001
                    },
                    "internal": {
                        "hi_freq_cutoff": 0.05,
                        "lo_freq_cutoff": 0.01
                    }
                }
            }
        },
        "exclude_genes": ['GENE3'],
        "frequencies": {
            "groups": {
                "external": {
                    "ExAC": ["G"],
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
                "exclude_filtering_existing_assessment": True
            }
        ]
    },
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
        change_type="SNP"
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

    g1 = gene.Gene(hugo_symbol="GENE1")
    g2 = gene.Gene(hugo_symbol="GENE2")
    g3 = gene.Gene(hugo_symbol="GENE3")

    t1 = gene.Transcript(
        gene=g1,
        refseq_name='NM_1.1',
        ensembl_id='ENST1',
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

    genepanel = gene.Genepanel(
        name='testpanel',
        version='v01',
        genome_reference='GRCh37',
        config=GP_CONFIG
    )

    genepanel.transcripts = [t1, t2, t3]
    return genepanel


class TestAlleleFilter(object):

    @pytest.mark.aa(order=0)
    def test_prepare_data(self, test_database, session):
        test_database.refresh()  # Reset db

        gp = create_genepanel(GP_CONFIG)
        session.add(gp)
        session.commit()

    @pytest.mark.aa(order=1)
    def test_frequency_filtering(self, session):

        # Filter config should end up being the following
        # (GENE2 has override in genepanel config, hence different threshold)
        # GENE1: external: 0.005/0.001 , internal: 0.05/0.01
        # GENE2: external: 0.5/0.1 , internal: 0.7/0.6
        # GENE3: Will be 'GENE' filtered


        ##
        # Test positive cases
        ##

        # Test external
        # GENE1: external: 0.005/0.001 , internal: 0.05/0.01
        pa1 = create_allele_annotation(session, {
            'frequencies': {
                'ExAC': {
                    'freq': {
                        'G': 0.0051   # Above 0.005
                    }
                }
            },
            'transcripts': [
                {
                    'symbol': 'GENE1',
                    'transcript': 'NM_1.1',
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
        # GENE1: external: 0.005/0.001 , internal: 0.05/0.01
        pa3 = create_allele_annotation(session, {
            'frequencies': {
                'ExAC': {
                    'freq': {
                        'G': 0.0051  # Above 0.005
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
                    'symbol': 'GENE1',
                    'transcript': 'NM_1.1',
                    'exon_distance': 0
                }
            ]
        })

        # Test right on threshold
        # GENE1: external: 0.005/0.001 , internal: 0.05/0.01
        pa4 = create_allele_annotation(session, {
            'frequencies': {
                'ExAC': {
                    'freq': {
                        'G': 0.005  # == 0.005
                    }
                }
            },
            'transcripts': [
                {
                    'symbol': 'GENE1',
                    'transcript': 'NM_1.1',
                    'exon_distance': 0
                }
            ]
        })

        session.commit()

        af = AlleleFilter(session, CONFIG)
        gp_key = ('testpanel', 'v01')
        allele_ids = [pa1.id, pa2.id, pa3.id, pa4.id]
        result = af.filter_alleles({gp_key: allele_ids})

        assert all(a in result[gp_key]['excluded_allele_ids']['frequency'] for a in allele_ids)

        ##
        # Test negative cases
        ##

        # Test external
        # GENE1: external: 0.005/0.001 , internal: 0.05/0.01
        na1 = create_allele_annotation(session, {
            'frequencies': {
                'ExAC': {
                    'freq': {
                        'G': 0.0049   # Below 0.005
                    }
                }
            },
            'transcripts': [
                {
                    'symbol': 'GENE1',
                    'transcript': 'NM_1.1',
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
                    'symbol': 'GENE1',
                    'transcript': 'NM_1.1',
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
                    }
                }
            },
            'transcripts': [
                {
                    'symbol': 'GENE1',
                    'transcript': 'NM_1.1',
                    'exon_distance': 0
                }
            ]
        })

        session.commit()

        af = AlleleFilter(session, CONFIG)
        gp_key = ('testpanel', 'v01')
        allele_ids = [na1.id, na2.id, na3.id, na4.id]
        result = af.filter_alleles({gp_key: allele_ids})

        assert all(a in result[gp_key]['allele_ids'] for a in allele_ids)

    @pytest.mark.aa(order=2)
    def test_intronic_filtering(self, session):

        # intronic_region [-10, 5]

        ##
        # Test positive cases
        ##

        pa1 = create_allele_annotation(session, {
            'transcripts': [
                {
                    'symbol': 'GENE1',
                    'transcript': 'NM_1.1',
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
                    'symbol': 'GENE1',
                    'transcript': 'NM_1.1',
                    'exon_distance': 10000000
                }
            ]
        })

        pa4 = create_allele_annotation(session, {
            'transcripts': [
                {
                    'symbol': 'GENE1',
                    'transcript': 'NM_1.1',
                    'exon_distance': -1000000
                }
            ]
        })

        session.commit()

        af = AlleleFilter(session, CONFIG)
        gp_key = ('testpanel', 'v01')
        allele_ids = [pa1.id, pa2.id, pa3.id, pa4.id]
        result = af.filter_alleles({gp_key: allele_ids})

        assert all(a in result[gp_key]['excluded_allele_ids']['intronic'] for a in allele_ids)

        ##
        # Test negative cases
        ##

        na1 = create_allele_annotation(session, {
            'transcripts': [
                {
                    'symbol': 'GENE1',
                    'transcript': 'NM_1.1',
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
                    'symbol': 'GENE1',
                    'transcript': 'NM_1.1',
                    'exon_distance': 0
                }
            ]
        })

        # Check that annotation transcripts are filtered properly on genepanel transcripts
        na4 = create_allele_annotation(session, {
            'transcripts': [
                {
                    'symbol': 'GENE1',
                    'transcript': 'NM_1.1',
                    'exon_distance': -1
                },
                {
                    'symbol': 'SOMEOTHERGENE',
                    'transcript': 'NOT_IN_GENEPANEL',
                    'exon_distance': 1000
                }
            ]
        })

        session.commit()

        af = AlleleFilter(session, CONFIG)
        gp_key = ('testpanel', 'v01')
        allele_ids = [na1.id, na2.id, na3.id, na4.id]
        result = af.filter_alleles({gp_key: allele_ids})

        assert all(a in result[gp_key]['allele_ids'] for a in allele_ids)

    @pytest.mark.aa(order=3)
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
                    'symbol': 'GENE1',
                    'transcript': 'NM_1.1',
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

        assert all(a in result[gp_key]['excluded_allele_ids']['gene'] for a in allele_ids)

        ##
        # Test negative cases
        ##

        na1 = create_allele_annotation(session, {
            'transcripts': [
                {
                    'symbol': 'GENE1',
                    'transcript': 'NM_1.1',
                }
            ]
        })

        na2 = create_allele_annotation(session, {
            'transcripts': [
                {
                    'symbol': 'GENE1',
                    'transcript': 'NM_1.1',
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

        assert all(a in result[gp_key]['allele_ids'] for a in allele_ids)


    @pytest.mark.aa(order=4)
    def test_filter_order(self, session):

        # Test filter order: gene -> frequency -> intronic

        # Will be filtered on frequency, gene and intronic
        a1 = create_allele_annotation(session, {
            'frequencies': {
                'ExAC': {
                    'freq': {
                        'G': 0.0051   # Above 0.005
                    }
                }
            },
            'transcripts': [
                {
                    'symbol': 'GENE3',
                    'transcript': 'NM_1.1',
                    'exon_distance': 1000
                }
            ]
        })

        # Will be filtered on frequency and intronic
        a2 = create_allele_annotation(session, {
            'frequencies': {
                'ExAC': {
                    'freq': {
                        'G': 0.0051   # Above 0.005
                    }
                }
            },
            'transcripts': [
                {
                    'symbol': 'NOTEXCLUDED',
                    'transcript': 'NM_1.1',
                    'exon_distance': 1000
                }
            ]
        })

        # Will be filtered on intronic only
        a3 = create_allele_annotation(session, {
            'frequencies': {
                'ExAC': {
                    'freq': {
                        'G': 0   # BELOW 0.005
                    }
                }
            },
            'transcripts': [
                {
                    'symbol': 'NOTEXCLUDED',
                    'transcript': 'NM_1.1',
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
