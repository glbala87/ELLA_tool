import copy
import logging

from api.config import config
#
from api.util.util import get_nested

INHERITANCE_GROUP_AD = 'AD'
INHERITANCE_GROUP_DEFAULT = 'default'

INHERITANCE_AD = 'AD'
INHERITANCE_AR = 'AR'
INHERITANCE_DEFAULT = INHERITANCE_AR

"""
Reads the gene panel specific config and overrides the default values if the gene panel config
defines gene-specific values
"""


def _choose_cutoff_group(cutoff_groups, inheritance_code):
    """
    Find the lo/hi cutoffs for internal and external databases using inheritance if present.

    There are generally two sets for cutoffs, one for AD and for non-AD.

    :param inheritance_code:
    :return: a dict with 'internal' and 'external' which contain lo and hi cutoffs
    """

    cutoff_group = INHERITANCE_GROUP_DEFAULT

    if inheritance_code:
        if not isinstance(inheritance_code, list):
            inheritance_code = [inheritance_code]

        codes = set(inheritance_code)
        if len(codes) == 1 and codes.pop().upper() == INHERITANCE_AD:
            cutoff_group = INHERITANCE_GROUP_AD

    return cutoff_groups[cutoff_group]


def _chose_inheritance(codes=None):
    if not codes:
        return INHERITANCE_DEFAULT
    if all(map(lambda c: c.upper() == INHERITANCE_AD, codes)):
        return INHERITANCE_AD
    else:
        return INHERITANCE_DEFAULT


class GenepanelConfigResolver(object):
    def __init__(self, genepanel=None, genepanel_default=None):
        """

        :param genepanel:
        :type genepanel: vardb.datamodel.gene.Genepanel
        :param genepanel_default: If None use the hardcoded defaults found in config.py (which is the normal case).
            Use non-None in when testing logic in unit tests.
        """
        super(GenepanelConfigResolver, self).__init__()
        self.genepanel = genepanel
        self.global_default = config['variant_criteria']['genepanel_config'] if not genepanel_default else genepanel_default

    def resolve(self, symbol):
        """
        Find the config values using any overrides that might be defined on the genepanel.
        Algorithm: start with a dict with default values and mutate it if more gene-specific info
        is available. The algorithm are described in stages (stage 1, stage 2 etc) for clarity.

        Inheritance is calculated based on the phenotypes' inheritance.

        Uses deepcopy to avoid any mutation of the "constants" of this module.

        Output will look something like:

        {'freq_num_thresholds': {...},
         'freq_cutoffs': {'external': {'hi_freq_cutoff': 0.01, 'lo_freq_cutoff': 1.0},
                          'internal': {'hi_freq_cutoff': 0.05, 'lo_freq_cutoff': 1.0}},
         'inheritance': 'AD',
         'disease_mode': 'ANY',
         'last_exon_important': True}


        :param symbol: Might be None
        :return: the values to be used by the rules engine/allele filter for this gene.
         The calculated values is based on global defaults and any overrides in the genepanel
        """

        # Stage 1: init the result using the global defaults for inheritance, disease_mode and last_exon_important
        # ('freq_cutoff_groups' has an extra level we don't return):
        result = copy.deepcopy(self.global_default)
        result.pop('freq_cutoff_groups', None)

        # Stage 2: find frequency cutoffs for 'default' from either genepanel or global:
        if not symbol:
            logging.warning("Symbol not defined when resolving genepanel config values")
            result['freq_cutoffs'] = copy.deepcopy(get_nested(self.global_default, 'freq_cutoff_groups', 'default'))
            if self.genepanel and self.genepanel.config:
                genepanel_cutoffs = get_nested(self.genepanel.config, 'data', 'freq_cutoff_groups', 'default')
                if genepanel_cutoffs:
                    result['freq_cutoffs'].update(genepanel_cutoffs)

            # only cutoffs are defined in gene-independent genepanel config. Others are taken from global, see above
            return copy.deepcopy(result)

        # if not self.genepanel:  # no panel to find any specific info
        #     logging.warning("Genepanel not defined when resolving genepanel config values")
        #     result["freq_cutoffs"] = self.genepanel_default["freq_cutoffs"]['default']
        #     return copy.deepcopy(result)

        # A specific symbol can define cutoffs, inheritance, disease_mode and last_exon_important
        # Stage 3: find the most "useful" inheritance using the gene symbol:
        chosen_inheritance = _chose_inheritance(self.genepanel.find_inheritance_codes(symbol))
        result['inheritance'] = chosen_inheritance

        # Stage 5: look for gene specific overrides:
        if self.genepanel and self.genepanel.config:
            gene_specific_overrides = copy.deepcopy(get_nested(self.genepanel.config, 'data', 'genes', symbol))
            if gene_specific_overrides and get_nested(gene_specific_overrides, "inheritance"):
                result['inheritance'] = _chose_inheritance(get_nested(gene_specific_overrides, "inheritance"))
                gene_specific_overrides.pop('inheritance', None)  # we expose a refined inheritance

            if gene_specific_overrides:
                result.update(gene_specific_overrides)

        # Stage 4: internal and external cutoffs from global config or genepanel config using inheritance:
        result['freq_cutoffs'] = copy.deepcopy(_choose_cutoff_group(self.global_default['freq_cutoff_groups'], result['inheritance']))
        # gene panel can define cutoffs overriding the global ones:
        genepanel_cutoff_groups = get_nested(self.genepanel.config, 'data', 'freq_cutoff_groups')
        if genepanel_cutoff_groups:
            print 'xxxx'
            print self.genepanel.config
            print genepanel_cutoff_groups
            genepanel_cutoffs = _choose_cutoff_group(genepanel_cutoff_groups, result['inheritance'])
            result['freq_cutoffs'].update(genepanel_cutoffs)

        # Stage 5: look for gene specific overrides:
        # if self.genepanel and self.genepanel.config:
        #     gene_specific_overrides = get_nested(self.genepanel.config, 'data', 'genes', symbol)
        #     result.update(gene_specific_overrides)

            # if gene specifies inheritance, use that instead of the one derived from the phenotypes:
            # if "inheritance" in gene_specific_overrides:
            #     result["freq_cutoffs"] = copy.deepcopy(_find_cutoffs(self.global_default['freq_cutoff_groups'], gene_specific_overrides["inheritance"]))

            # copy over any freq_cutoffs overrides from genepanel config
            # the overrides might be partial, so we need to check each group individually
            # instead of copying all of 'freq_cutoffs'
            # if 'freq_cutoffs' in gene_specific_overrides:
            #     for freq_group in config['variant_criteria']['frequencies']['groups'].keys():  # currently external and internal
            #         if freq_group in gene_specific_overrides['freq_cutoffs']:
            #             result['freq_cutoffs'][freq_group] = gene_specific_overrides['freq_cutoffs'][freq_group]

        return copy.deepcopy(result)

    def config_isolated(self): # the config element of this panel
        return copy.deepcopy(self.genepanel.config)

    def config_merged(self): # the combined config of this panel and global default
        m = copy.deepcopy(self.global_default)
        m.update(self.genepanel.config)
        return m

    def get_AD_freq_cutoffs(self):
        return self.global_default["freq_cutoff_groups"]['AD']

    def get_default_freq_cutoffs(self):
        return self.global_default["freq_cutoff_groups"]['default']

    def get_genes_with_overrides(self):
        if self.genepanel.config and get_nested(self.genepanel.config, 'data', 'genes'):
            return get_nested(self.genepanel.config, 'data', 'genes').keys()

        return list()
