import copy
import logging

from api.util import queries

from api.util.util import dict_merge

INHERITANCE_GROUP_AD = "AD"
INHERITANCE_GROUP_DEFAULT = "default"


def _choose_cutoff_group(cutoff_groups, is_ad=False):
    """
    Find the lo/hi cutoffs for internal and external databases.

    There are generally two sets for cutoffs, one for AD and for non-AD.

    :param is_ad: Whether the inheritance is AD or not
    :return: a dict with 'internal' and 'external' which contain lo and hi cutoffs
    """

    if is_ad:
        return cutoff_groups[INHERITANCE_GROUP_AD]
    else:
        return cutoff_groups[INHERITANCE_GROUP_DEFAULT]


class AcmgConfig(object):
    """
    Find parameters needed for rule engine.
    """

    def __init__(self, session, acmgconfig, genepanel=None):
        """
        :param acmgconfig: Config for ACMG rule engine. Normally set in user(group) config.
        :param genepanel: Genepanel for checking inheritance mode.
        :type genepanel: vardb.datamodel.gene.Genepanel
        """
        self.session = session
        self.genepanel = genepanel
        self.acmgconfig = acmgconfig
        self._ad_hgnc_ids_cache = None  # Holds cache for inheritance per hgnc_id
        self._ar_hgnc_ids_cache = None  # Holds cache for inheritance per hgnc_id

    def get_commoness_config(self):
        """
        Create config for use in the commoness filter in FrequencyFilter

        Converts
        {
            "frequency": {
                "thresholds": {
                    "AD": {
                        "external": { "hi_freq_cutoff": 0.005, "lo_freq_cutoff": 0.001 },
                        "internal": { "hi_freq_cutoff": 0.05, "lo_freq_cutoff": 1.0 }
                    },
                    "default": {
                        "external": { "hi_freq_cutoff": 0.01, "lo_freq_cutoff": 1.0 },
                        "internal": { "hi_freq_cutoff": 0.05, "lo_freq_cutoff": 1.0 }
                    }
                }
            },
            ....
            "genes": {
                "1101": {
                    "frequency": {
                        "thresholds": {
                            "external": { "hi_freq_cutoff": 0.008, "lo_freq_cutoff": 0.0005 },
                            "internal": { "hi_freq_cutoff": 0.008, "lo_freq_cutoff": 0.0005 }
                        }
                    },
                    ....
                }
            }
        }

        into

        {
            "frequency": {
                "thresholds": {
                    "AD": {
                        "external": { "hi_freq_cutoff": 0.005, "lo_freq_cutoff": 0.001 },
                        "internal": { "hi_freq_cutoff": 0.05, "lo_freq_cutoff": 1.0 }
                    },
                    "default": {
                        "external": { "hi_freq_cutoff": 0.01, "lo_freq_cutoff": 1.0 },
                        "internal": { "hi_freq_cutoff": 0.05, "lo_freq_cutoff": 1.0 }
                    }
                },
                "genes": {
                    "1101": {
                        "frequency": {
                            "thresholds": {
                                "external": { "hi_freq_cutoff": 0.008, "lo_freq_cutoff": 0.0005 },
                                "internal": { "hi_freq_cutoff": 0.008, "lo_freq_cutoff": 0.0005 }
                            }
                        }
                    }
                }
            }
        }
        """
        frequency_config = copy.deepcopy(self.acmgconfig["frequency"])
        per_gene_config = copy.deepcopy(self.acmgconfig.get("genes", {}))

        for hgnc_id, override in per_gene_config.items():
            if "frequency" in override:
                if "genes" not in frequency_config:
                    frequency_config["genes"] = dict()
                frequency_config["genes"][hgnc_id] = override["frequency"]

        return frequency_config

    def resolve(self, hgnc_id):
        """
        Find the config values using any overrides that might be defined on the acmgconfig.
        Algorithm: start with a dict with default values and mutate it if more gene-specific info
        is available. The algorithm are described in stages (stage 1, stage 2 etc) for clarity.

        Inheritance is calculated based on the phenotypes' inheritance.

        Uses deepcopy to avoid any mutation of the "constants" of this module.

        Output will look something like:

        {
         'freq_cutoffs': {'external': {'hi_freq_cutoff': 0.01, 'lo_freq_cutoff': 1.0},
                          'internal': {'hi_freq_cutoff': 0.05, 'lo_freq_cutoff': 1.0}},
         'inheritance': 'AD',
         'disease_mode': 'ANY',
         'last_exon_important': True
        }

        :param hgnc_id: Might be None
        :return: the values to be used by the rules engine for this gene.
        """

        # Deep copy the result from the provided defaults
        result_config = copy.deepcopy(self.acmgconfig)
        # Pop the data that's not part of final result
        frequency_config = result_config.pop("frequency")
        per_gene_config = result_config.pop("genes", {})
        # HGNC ids must be int, but source might have strings from JSON data
        per_gene_config = {int(k): v for k, v in per_gene_config.items()}

        if not hgnc_id:
            # If there's no hgnc_id, use frequency cutoffs for 'default'
            logging.warning("hgnc_id not defined when resolving genepanel config values")
            result_config["freq_cutoffs"] = frequency_config["thresholds"]["default"]
        else:
            hgnc_id = int(hgnc_id)
            # Find the inheritance 'mode' (AD, AR or neither) for the provided hgnc_id:
            # These are cached in case of subsequent calls to this function
            if self._ad_hgnc_ids_cache is None:
                ad_hgnc_ids = queries.distinct_inheritance_hgnc_ids_for_genepanel(
                    self.session, "AD", self.genepanel.name, self.genepanel.version
                ).all()
                self._ad_hgnc_ids_cache = list(set([a[0] for a in ad_hgnc_ids]))

            if self._ar_hgnc_ids_cache is None:
                ar_hgnc_ids = queries.distinct_inheritance_hgnc_ids_for_genepanel(
                    self.session, "AR", self.genepanel.name, self.genepanel.version
                ).all()
                self._ar_hgnc_ids_cache = list(set([a[0] for a in ar_hgnc_ids]))

            # Add inheritance, used by rule engine:
            assert not (hgnc_id in self._ad_hgnc_ids_cache and hgnc_id in self._ar_hgnc_ids_cache)
            if hgnc_id in self._ad_hgnc_ids_cache:
                result_config["inheritance"] = "AD"
            if hgnc_id in self._ar_hgnc_ids_cache:
                result_config["inheritance"] = "AR"

            # Add the relevant frequency cutoff for this inheritance (AD/default)
            result_config["freq_cutoffs"] = copy.deepcopy(
                _choose_cutoff_group(
                    frequency_config["thresholds"], hgnc_id in self._ad_hgnc_ids_cache
                )
            )

            # Look for any gene specific overrides for this hgnc_id:
            if per_gene_config and hgnc_id in per_gene_config:
                gene_specific_overrides = per_gene_config[hgnc_id]

                # Handle frequency specially
                if "frequency" in gene_specific_overrides:
                    gene_frequency_config = gene_specific_overrides.pop("frequency")
                    result_config["freq_cutoffs"] = gene_frequency_config["thresholds"]

                # Merge the remaining
                dict_merge(result_config, gene_specific_overrides)

        return result_config
