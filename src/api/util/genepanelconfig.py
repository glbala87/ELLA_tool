import copy
import logging

from api.config import config
from api.util import queries

#
from api.util.util import get_nested, dict_merge

INHERITANCE_GROUP_AD = 'AD'
INHERITANCE_GROUP_DEFAULT = 'default'


"""
Reads the gene panel specific config and overrides the default values if the gene panel config
defines gene-specific values
"""


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


class GenepanelConfigResolver(object):
    """
    Find parameters needed in variant filtering and rule engine. The genepanel can have it's own configuration that
    overrides values defined globally.
    """

    def __init__(self, session, genepanel=None, genepanel_default=None):
        """

        :param genepanel:
        :type genepanel: vardb.datamodel.gene.Genepanel
        :param genepanel_default: If None use the hardcoded defaults found in config.py (which is the normal case).
            Use non-None in when testing logic in unit tests.
        """
        super(GenepanelConfigResolver, self).__init__()
        self.session = session
        self.genepanel = genepanel
        self.global_default = config['variant_criteria']['genepanel_config'] if not genepanel_default else genepanel_default
        self._ad_genes_cache = []  # Holds cache for inheritance per symbol
        self._ar_genes_cache = []  # Holds cache for inheritance per symbol

    def resolve(self, symbol):
        """
        Find the config values using any overrides that might be defined on the genepanel.
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

        :param symbol: Might be None
        :return: the values to be used by the rules engine/allele filter for this gene.


         The calculated values is based on global defaults and any overrides in the genepanel.
         The global and genepanel config have dict with the same keys, so we can merge
         the dicts to implement to override logic.
        """

        # Stage 1: init the result using the global defaults
        config_storage = copy.deepcopy(self.global_default)

        if self.genepanel and self.genepanel.config:
            dict_merge(config_storage, self.genepanel.config['data'])
            del config_storage['genes']

        # Stage 2: find frequency cutoffs for 'default' from either genepanel or global:
        if not symbol:
            logging.warning("Symbol not defined when resolving genepanel config values")
            config_storage['freq_cutoffs'] = get_nested(config_storage, ['freq_cutoff_groups', 'default'])
        else:
            # A specific symbol can define cutoffs, disease_mode and last_exon_important
            # Stage 3: find the most "useful" inheritance using the gene symbol:
            if not self._ad_genes_cache:
                ad_genes = queries.distinct_inheritance_genes_for_genepanel(
                    self.session,
                    'AD',
                    self.genepanel.name,
                    self.genepanel.version
                ).all()
                self._ad_genes_cache = list(set([a[0] for a in ad_genes]))

            if not self._ar_genes_cache:
                ar_genes = queries.distinct_inheritance_genes_for_genepanel(
                    self.session,
                    'AR',
                    self.genepanel.name,
                    self.genepanel.version
                ).all()
                self._ar_genes_cache = list(set([a[0] for a in ar_genes]))

            # Add inheritance, used by rule engine
            assert not (symbol in self._ad_genes_cache and symbol in self._ar_genes_cache)
            if symbol in self._ad_genes_cache:
                config_storage['inheritance'] = 'AD'
            if symbol in self._ar_genes_cache:
                config_storage['inheritance'] = 'AR'

            config_storage['freq_cutoffs'] = copy.deepcopy(
                _choose_cutoff_group(config_storage['freq_cutoff_groups'], symbol in self._ad_genes_cache))

            # Stage 5: look for gene specific overrides:
            gene_specific_overrides = copy.deepcopy(get_nested(self.genepanel.config, ['data', 'genes', symbol]))
            if gene_specific_overrides:
                dict_merge(config_storage, gene_specific_overrides)

        config_storage.pop('freq_cutoff_groups', None)
        return config_storage

    def get_AD_freq_cutoffs(self):
        return self.global_default["freq_cutoff_groups"]['AD']

    def get_default_freq_cutoffs(self):
        return self.global_default["freq_cutoff_groups"]['default']

    def get_genes_with_overrides(self):
        if self.genepanel.config and get_nested(self.genepanel.config, ['data', 'genes']):
            return get_nested(self.genepanel.config, ['data', 'genes']).keys()

        return list()
