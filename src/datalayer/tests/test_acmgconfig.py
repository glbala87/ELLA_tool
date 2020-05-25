from sqlalchemy import tuple_
from datalayer.acmgconfig import AcmgConfig
from vardb.datamodel import gene


def test_resolver_uses_acmgconfig_defined_cutoffs(session):

    # HBOCUTV v01 contains BRCA2 and has no defined config
    acmgconfig = {
        "disease_mode": "TEST_ANY",
        "last_exon_important": "TEST_LEI",
        "frequency": {
            "thresholds": {
                "AD": {
                    "external": {  # 'external'/'internal' references the groups under 'frequencies->groups' key below
                        "hi_freq_cutoff": 0.123,
                        "lo_freq_cutoff": 0.321,
                    },
                    "internal": {"hi_freq_cutoff": 0.456, "lo_freq_cutoff": 0.654},
                },
                "default": {
                    "external": {"hi_freq_cutoff": 0.789, "lo_freq_cutoff": 0.987},
                    "internal": {"hi_freq_cutoff": 0.147, "lo_freq_cutoff": 0.741},
                },
            }
        },
    }

    genepanel = (
        session.query(gene.Genepanel)
        .filter(tuple_(gene.Genepanel.name, gene.Genepanel.version) == ("HBOCUTV", "v01"))
        .one()
    )

    resolver = AcmgConfig(session, acmgconfig, genepanel=genepanel)
    props = resolver.resolve(1502)

    assert (
        props["freq_cutoffs"]["external"]["hi_freq_cutoff"]
        == acmgconfig["frequency"]["thresholds"]["default"]["external"]["hi_freq_cutoff"]
    )
    assert (
        props["freq_cutoffs"]["external"]["lo_freq_cutoff"]
        == acmgconfig["frequency"]["thresholds"]["default"]["external"]["lo_freq_cutoff"]
    )
    assert (
        props["freq_cutoffs"]["internal"]["hi_freq_cutoff"]
        == acmgconfig["frequency"]["thresholds"]["default"]["internal"]["hi_freq_cutoff"]
    )
    assert (
        props["freq_cutoffs"]["internal"]["lo_freq_cutoff"]
        == acmgconfig["frequency"]["thresholds"]["default"]["internal"]["lo_freq_cutoff"]
    )
    assert props["disease_mode"] == acmgconfig["disease_mode"]
    assert props["last_exon_important"] == acmgconfig["last_exon_important"]

    # HBOCUTV v01 contains BRCA2
    acmgconfig = {
        "disease_mode": "PANELLEVEL_ANY",
        "last_exon_important": "PANELLEVEL_LEI",
        "frequency": {
            "thresholds": {
                "AD": {
                    "external": {  # 'external'/'internal' references the groups under 'frequencies->groups' key below
                        "hi_freq_cutoff": 0.123,
                        "lo_freq_cutoff": 0.321,
                    },
                    "internal": {"hi_freq_cutoff": 0.456, "lo_freq_cutoff": 0.654},
                },
                "default": {
                    "external": {"hi_freq_cutoff": 0.789, "lo_freq_cutoff": 0.987},
                    "internal": {"hi_freq_cutoff": 0.147, "lo_freq_cutoff": 0.741},
                },
            }
        },
        "genes": {
            "1101": {
                "inheritance": "GENELEVEL_AD",
                "disease_mode": "GENELEVEL_ANY",
                "last_exon_important": "GENELEVEL_LEI",
                "frequency": {
                    "thresholds": {
                        "external": {"hi_freq_cutoff": 0.55, "lo_freq_cutoff": 0.45},
                        "internal": {"hi_freq_cutoff": 0.33, "lo_freq_cutoff": 0.22},
                    }
                },
            }
        },
    }

    # Check that gene overrides are used
    resolver = AcmgConfig(session, acmgconfig, genepanel=genepanel)
    props = resolver.resolve(1101)

    assert (
        props["freq_cutoffs"]["external"]["hi_freq_cutoff"]
        == acmgconfig["genes"]["1101"]["frequency"]["thresholds"]["external"]["hi_freq_cutoff"]
    )
    assert (
        props["freq_cutoffs"]["external"]["lo_freq_cutoff"]
        == acmgconfig["genes"]["1101"]["frequency"]["thresholds"]["external"]["lo_freq_cutoff"]
    )
    assert (
        props["freq_cutoffs"]["internal"]["hi_freq_cutoff"]
        == acmgconfig["genes"]["1101"]["frequency"]["thresholds"]["internal"]["hi_freq_cutoff"]
    )
    assert (
        props["freq_cutoffs"]["internal"]["lo_freq_cutoff"]
        == acmgconfig["genes"]["1101"]["frequency"]["thresholds"]["internal"]["lo_freq_cutoff"]
    )
    assert props["disease_mode"] == acmgconfig["genes"]["1101"]["disease_mode"]
    assert props["last_exon_important"] == acmgconfig["genes"]["1101"]["last_exon_important"]
