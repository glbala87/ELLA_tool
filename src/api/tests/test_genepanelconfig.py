from sqlalchemy import tuple_
from api.util.genepanelconfig import GenepanelConfigResolver
from vardb.datamodel import gene


DEFAULT_CONFIG = {
    "freq_cutoff_groups": {
        "AD": {
            "external": {  # 'external'/'internal' references the groups under 'frequencies->groups' key below
                "hi_freq_cutoff": 0.005,
                "lo_freq_cutoff": 0.001
            },
            "internal": {
                "hi_freq_cutoff": 0.05,
                "lo_freq_cutoff": 1.0
            }
        },
        "default": {
            "external": {
                "hi_freq_cutoff": 0.01,
                "lo_freq_cutoff": 1.0
            },
            "internal": {
                "hi_freq_cutoff": 0.05,
                "lo_freq_cutoff": 1.0
            }
        }
    },
    "disease_mode": "ANY",
    "last_exon_important": "LEI",
}


def test_resolver_uses_genepanel_defined_cutoffs(session):

    # HBOCUTV v01 contains BRCA2 and has no defined config
    config = {
        'data': {
            "disease_mode": "PANELLEVEL_ANY",
            "last_exon_important": "PANELLEVEL_LEI",
            "freq_cutoff_groups": {
                "AD": {
                    "external": {  # 'external'/'internal' references the groups under 'frequencies->groups' key below
                        "hi_freq_cutoff": 0.123,
                        "lo_freq_cutoff": 0.321
                    },
                    "internal": {
                        "hi_freq_cutoff": 0.456,
                        "lo_freq_cutoff": 0.654
                    }
                },
                "default": {
                    "external": {
                        "hi_freq_cutoff": 0.789,
                        "lo_freq_cutoff": 0.987
                    },
                    "internal": {
                        "hi_freq_cutoff": 0.147,
                        "lo_freq_cutoff": 0.741
                    }
                }
            },
            'genes': {
                'BRCA2': {
                    "inheritance": "GENELEVEL_AD",
                    "disease_mode": "GENELEVEL_ANY",
                    "last_exon_important": "GENELEVEL_LEI",
                    'freq_cutoffs': {
                        'external': {
                            'hi_freq_cutoff': 0.55,
                            'lo_freq_cutoff': 0.45
                        },
                        'internal': {
                            'hi_freq_cutoff': 0.33,
                            'lo_freq_cutoff': 0.22
                        }
                    }
                }
            }
        }
    }

    genepanel = session.query(gene.Genepanel).filter(
        tuple_(gene.Genepanel.name, gene.Genepanel.version) == ('HBOCUTV', 'v01')
    ).one()
    genepanel.config = {}

    # Check that defaults are used
    resolver = GenepanelConfigResolver(session, genepanel, genepanel_default=DEFAULT_CONFIG)
    props = resolver.resolve('NOTINCONFIG')

    assert props['freq_cutoffs']['external']['hi_freq_cutoff'] == DEFAULT_CONFIG['freq_cutoff_groups']['default']['external']['hi_freq_cutoff']
    assert props['freq_cutoffs']['external']['lo_freq_cutoff'] == DEFAULT_CONFIG['freq_cutoff_groups']['default']['external']['lo_freq_cutoff']
    assert props['freq_cutoffs']['internal']['hi_freq_cutoff'] == DEFAULT_CONFIG['freq_cutoff_groups']['default']['internal']['hi_freq_cutoff']
    assert props['freq_cutoffs']['internal']['lo_freq_cutoff'] == DEFAULT_CONFIG['freq_cutoff_groups']['default']['internal']['lo_freq_cutoff']
    assert props['disease_mode'] == DEFAULT_CONFIG['disease_mode']
    assert props['last_exon_important'] == DEFAULT_CONFIG['last_exon_important']

    # Check that panel level config is used
    genepanel.config = config
    resolver = GenepanelConfigResolver(session, genepanel, genepanel_default=DEFAULT_CONFIG)
    props = resolver.resolve('NOTINCONFIG')

    assert props['freq_cutoffs']['external']['hi_freq_cutoff'] == config['data']['freq_cutoff_groups']['default']['external']['hi_freq_cutoff']
    assert props['freq_cutoffs']['external']['lo_freq_cutoff'] == config['data']['freq_cutoff_groups']['default']['external']['lo_freq_cutoff']
    assert props['freq_cutoffs']['internal']['hi_freq_cutoff'] == config['data']['freq_cutoff_groups']['default']['internal']['hi_freq_cutoff']
    assert props['freq_cutoffs']['internal']['lo_freq_cutoff'] == config['data']['freq_cutoff_groups']['default']['internal']['lo_freq_cutoff']
    assert props['disease_mode'] == config['data']['disease_mode']
    assert props['last_exon_important'] == config['data']['last_exon_important']

    # Check that gene overrides are used
    props = resolver.resolve('BRCA2')

    assert props['freq_cutoffs']['external']['hi_freq_cutoff'] == config['data']['genes']['BRCA2']['freq_cutoffs']['external']['hi_freq_cutoff']
    assert props['freq_cutoffs']['external']['lo_freq_cutoff'] == config['data']['genes']['BRCA2']['freq_cutoffs']['external']['lo_freq_cutoff']
    assert props['freq_cutoffs']['internal']['hi_freq_cutoff'] == config['data']['genes']['BRCA2']['freq_cutoffs']['internal']['hi_freq_cutoff']
    assert props['freq_cutoffs']['internal']['lo_freq_cutoff'] == config['data']['genes']['BRCA2']['freq_cutoffs']['internal']['lo_freq_cutoff']
    assert props['disease_mode'] == config['data']['genes']['BRCA2']['disease_mode']
    assert props['last_exon_important'] == config['data']['genes']['BRCA2']['last_exon_important']
