import copy
import logging

from api.config import config
#
INHERITANCE_AD = 'AD'
INHERITANCE_AR = 'AR'
INHERITANCE_DEFAULT = INHERITANCE_AR

"""
Reads the gene panel specific config and overrides the default values if the gene panel config
defines gene-specific values
"""


def _find_cutoffs(genepanel_config, inheritance_code):
    """
    Find the lo/hi cutoffs using inheritance if present. There are generally two sets for cutoffs, one for AD
    and for non-AD. The default cutoffs can be overridden in the genepanel, in that case the cutoffs are

    :param inheritance_code:
    :return: a dict with lo and hi cutoffs
    """

    # Unless inheritance is unambigously AD, we use the 'default' group
    cutoff_group = 'default'

    if inheritance_code:
        if not isinstance(inheritance_code, list):
            inheritance_code = [inheritance_code]

        codes = set(inheritance_code)
        if len(codes) == 1 and codes.pop().upper() == INHERITANCE_AD:
            cutoff_group = INHERITANCE_AD

    return genepanel_config['freq_cutoffs'][cutoff_group]


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
        :param genepanel_default: If None use the hardcoded defaults (which is the normal case).
            Use non-None in when testing logic in unit tests.
        """
        super(GenepanelConfigResolver, self).__init__()
        self.genepanel = genepanel
        self.genepanel_default = config['variant_criteria']['genepanel_config'] if not genepanel_default else genepanel_default

    def resolve(self, symbol):
        """
        Find the config values using any overrides that might be defined on the genepanel.
        Algorithm: start with a dict with default values and mutate it if more gene-specific info
        is available. The algorithm are described in stages (stage 1, stage 2 etc) for clarity.

        Regarding 'freq_cutoffs':
        One thing to be aware of it that the the configuration file has inheritance (AD or default) as
        part of it's freq_cutoffs options, while the genepanel configs do not.
        Reason for this is that the genepanel configuration is supposed to force thresholds, regardless
        of inheritance mode, so inheritance is not relevant for the genepanel overrides.

        Inheritance is calculated based on the phenotypes' inheritance. If no phenotypes, we uses a default inheritance.

        Uses deepcopy to avoid any mutation of the "constants" of this module.

        Output will look something like:

        {'disease_mode': 'ANY',
         'freq_cutoffs': {'external': {'hi_freq_cutoff': 0.01, 'lo_freq_cutoff': 1.0},
                          'internal': {'hi_freq_cutoff': 0.05, 'lo_freq_cutoff': 1.0}},
         'inheritance': 'AD',
         'last_exon': True}


        :param symbol:
        :return: the values to be used by the rules engine. The genepanel can have gene specific values
         that will override the global defaults.
        """

        # Stage 1: init the result using the defaults
        result = dict(self.genepanel_default)

        # Stage 2: find frequency cutoffs when we don't have any specific info:
        if not symbol:
            logging.warning("Symbol not defined when resolving genepanel config values")
            result["freq_cutoffs"] = self.genepanel_default["freq_cutoffs"]['default']
            return copy.deepcopy(result)

        if not self.genepanel:  # no panel to find any specific info
            logging.warning("Genepanel not defined when resolving genepanel config values")
            result["freq_cutoffs"] = self.genepanel_default["freq_cutoffs"]['default']
            return copy.deepcopy(result)

        # Stage 3: find the most "useful" inheritance using the gene symbol:
        chosen_inheritance = _chose_inheritance(self.genepanel.find_inheritance(symbol))
        if chosen_inheritance:
            result['inheritance'] = chosen_inheritance

        # Stage 4: find/override cutoffs using inheritance:
        # Remove the AD/default level from freq_cutoffs {'external': {'AD': cutoffs, 'default': cutoffs}} -> {'external': AD_or_default_cutoffs}
        result["freq_cutoffs"] = copy.deepcopy(_find_cutoffs(self.genepanel_default, result['inheritance']))

        # Stage 5: allow any overrides defined in the gene panel config to win:
        if self.genepanel.config and 'data' in self.genepanel.config and symbol in self.genepanel.config['data']:
            gene_specific_overrides = self.genepanel.config['data'][symbol]
            result.update(gene_specific_overrides)

            # use inheritance to find cutoffs:
            if "inheritance" in gene_specific_overrides:
                result["freq_cutoffs"] = copy.deepcopy(_find_cutoffs(self.genepanel_default, gene_specific_overrides["inheritance"]))

            # copy over any freq_cutoffs overrides from genepanel config
            # the overrides might be partial, so we need to check each group individually
            # instead of copying all of 'freq_cutoffs'
            if 'freq_cutoffs' in gene_specific_overrides:
                for freq_group in config['variant_criteria']['frequencies']['groups'].keys():
                    if freq_group in gene_specific_overrides['freq_cutoffs']:
                        result['freq_cutoffs'][freq_group] = gene_specific_overrides['freq_cutoffs'][freq_group]

        return copy.deepcopy(result)

    def get_AD_freq_cutoffs(self):
        return self.genepanel_default["freq_cutoffs"]['AD']

    def get_default_freq_cutoffs(self):
        return self.genepanel_default["freq_cutoffs"]['default']

    def get_genes_with_overrides(self):

        if self.genepanel.config and 'data' in self.genepanel.config:
            return self.genepanel.config['data'].keys()

        return list()
