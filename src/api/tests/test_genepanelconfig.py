from sqlalchemy import tuple_
from api.util.genepanelconfig import GenepanelConfigResolver
from vardb.datamodel import gene


DEFAULT_CONFIG = {
    "freq_cutoffs": {
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
    "inheritance": "AD",
    "disease_mode": "ANY",
    "last_exon_important": "LEI",
}


def test_resolver_uses_genepanel_defined_cutoffs(session):

    # HBOCUTV v01 contains BRCA2 and has no defined config
    config = {
        'data': {
            'genes': {
                'BRCA2': {
                    'freq_cutoffs': {
                        'external': {
                            'hi_freq_cutoff': 0.9,
                            'lo_freq_cutoff': 0.8
                        },
                        'internal': {
                            'hi_freq_cutoff': 0.4,
                            'lo_freq_cutoff': 0.3
                        }
                    }
                }
            }
        }
    }

    genepanel = session.query(gene.Genepanel).filter(
        tuple_(gene.Genepanel.name, gene.Genepanel.version) == ('HBOCUTV', 'v01')
    ).one()
    genepanel.config = config

    resolver = GenepanelConfigResolver(session, genepanel, genepanel_default=DEFAULT_CONFIG)

    # Check that defaults are used
    props = resolver.resolve('NOTINCONFIG')

    assert props['freq_cutoffs']['external']['hi_freq_cutoff'] == DEFAULT_CONFIG['freq_cutoffs']['default']['external']['hi_freq_cutoff']
    assert props['freq_cutoffs']['external']['lo_freq_cutoff'] == DEFAULT_CONFIG['freq_cutoffs']['default']['external']['lo_freq_cutoff']
    assert props['freq_cutoffs']['internal']['hi_freq_cutoff'] == DEFAULT_CONFIG['freq_cutoffs']['default']['internal']['hi_freq_cutoff']
    assert props['freq_cutoffs']['internal']['lo_freq_cutoff'] == DEFAULT_CONFIG['freq_cutoffs']['default']['internal']['lo_freq_cutoff']

    # Check that gene overrides works are used
    props = resolver.resolve('BRCA2')

    assert props['freq_cutoffs']['external']['hi_freq_cutoff'] == 0.9
    assert props['freq_cutoffs']['external']['lo_freq_cutoff'] == 0.8
    assert props['freq_cutoffs']['internal']['hi_freq_cutoff'] == 0.4
    assert props['freq_cutoffs']['internal']['lo_freq_cutoff'] == 0.3
