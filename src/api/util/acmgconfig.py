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


class AcmgConfig(object):
    """
    Find parameters needed for rule engine.
    """

    def __init__(self, session, acmgconfig, genepanel=None):
        """

        :param genepanel: Genepanel for checking inheritance mode.
        :type genepanel: vardb.datamodel.gene.Genepanel

        """
        self.session = session
        self.genepanel = genepanel
        self.acmgconfig = acmgconfig
        self._ad_hgnc_ids_cache = None  # Holds cache for inheritance per hgnc_id
        self._ar_hgnc_ids_cache = None  # Holds cache for inheritance per hgnc_id

    def resolve(self, hgnc_id):
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

        :param hgnc_id: Might be None
        :return: the values to be used by the rules engine/allele filter for this gene.


         The calculated values is based on global defaults and any overrides in the genepanel.
         The global and genepanel config have dict with the same keys, so we can merge
         the dicts to implement to override logic.
        """

        # Stage 1: init the result using the global defaults
        result_config = copy.deepcopy(self.acmgconfig)
        per_gene_config = result_config.pop('genes', {})

        # HGNC ids must be int, but source might have strings from JSON data
        per_gene_config = {int(k): v for k, v in per_gene_config.iteritems()}
        # Stage 2: find frequency cutoffs for 'default' from either genepanel or global:
        if not hgnc_id:
            logging.warning("hgnc_id not defined when resolving genepanel config values")
            result_config['freq_cutoffs'] = result_config['frequency']['thresholds']['default']
        else:
            hgnc_id = int(hgnc_id)
            # A specific hgnc_id can define cutoffs, disease_mode and last_exon_important
            # Stage 3: find the most "useful" inheritance using the gene hgnc_id:
            if self._ad_hgnc_ids_cache is None:
                ad_hgnc_ids = queries.distinct_inheritance_hgnc_ids_for_genepanel(
                    self.session,
                    'AD',
                    self.genepanel.name,
                    self.genepanel.version
                ).all()
                self._ad_hgnc_ids_cache = list(set([a[0] for a in ad_hgnc_ids]))

            if self._ar_hgnc_ids_cache is None:
                ar_hgnc_ids = queries.distinct_inheritance_hgnc_ids_for_genepanel(
                    self.session,
                    'AR',
                    self.genepanel.name,
                    self.genepanel.version
                ).all()
                self._ar_hgnc_ids_cache = list(set([a[0] for a in ar_hgnc_ids]))

            # Add inheritance, used by rule engine
            assert not (hgnc_id in self._ad_hgnc_ids_cache and hgnc_id in self._ar_hgnc_ids_cache)
            if hgnc_id in self._ad_hgnc_ids_cache:
                result_config['inheritance'] = 'AD'
            if hgnc_id in self._ar_hgnc_ids_cache:
                result_config['inheritance'] = 'AR'

            result_config['freq_cutoffs'] = copy.deepcopy(
                _choose_cutoff_group(result_config['frequency']['thresholds'], hgnc_id in self._ad_hgnc_ids_cache))

            # Stage 5: look for gene specific overrides:
            if per_gene_config and hgnc_id in per_gene_config:
                gene_specific_overrides = per_gene_config[hgnc_id]
                dict_merge(result_config, gene_specific_overrides)
                result_config['freq_cutoffs'] = result_config['frequency']['thresholds']

        result_config.pop('frequency', None)
        return result_config

    def get_AD_thresholds(self):
        return self.acmgconfig["thresholds"]['AD']

    def get_default_thresholds(self):
        return self.acmgconfig["thresholds"]['default']

    def get_genes_with_overrides(self):
        if get_nested(self.acmgconfig, ['data', 'genes']):
            return get_nested(self.acmgconfig, ['data', 'genes']).keys()

        return list()
