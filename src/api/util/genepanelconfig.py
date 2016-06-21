import logging
import copy

# Global config values that can be overridden by gene panels.
KEY_INHERITANCE = 'inheritance'
KEY_LO = "lo_freq_cutoff"
KEY_HI = "hi_freq_cutoff"
KEY_CUTOFFS = "freq_cutoffs"

# values defined in Excel file WebUI_config_rules
DEFAULT_CUTOFFS = {KEY_HI: 0.01, KEY_LO: 1.0}
AD_CUTOFFS = {KEY_HI: 0.005, KEY_LO: 0.001}

COMMON_GENEPANEL_CONFIG = {
    KEY_CUTOFFS: {
        "AD": AD_CUTOFFS,
        "Other": DEFAULT_CUTOFFS
    },
    KEY_INHERITANCE: "AD",
    "disease_mode": "ANY",
    "last_exon": True,
}

"""
Reads the gene panel specific config and overrides the default values if the gene panel config
defines gene-specific values
"""


def _find_cutoffs(inheritance_code):
    """
    Find the lo/hi cutoffs using inheritance if present. There are generally two sets for cutoffs, one for AD
    and for non-AD. The default cutoffs can be overridden in the genepanel, in that case the cutoffs are

    :param inheritance_code:
    :return: a dict with lo and hi cutoffs
    """

    if not inheritance_code:
        return DEFAULT_CUTOFFS

    if isinstance(inheritance_code, list):
        codes = set(inheritance_code)
        if len(codes) > 1:  # multiple inheritance codes. Don't look in genepanel.
            return DEFAULT_CUTOFFS
        if codes.pop().upper() == 'AD':
            return COMMON_GENEPANEL_CONFIG[KEY_CUTOFFS]["AD"]
        else:
            return DEFAULT_CUTOFFS
    else:
        if inheritance_code.upper() == 'AD':
            return COMMON_GENEPANEL_CONFIG[KEY_CUTOFFS]["AD"]

    return DEFAULT_CUTOFFS


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
        self.genepanel_default = COMMON_GENEPANEL_CONFIG if not genepanel_default else genepanel_default

    def resolve(self, symbol):
        """
        Find the config values using any overrides that might be defined on the genepanel.
        Algorithm: start with a dict with default values and mutate it if more gene-specific info
        is available.

        Uses deepcopy to avoid any mutation of the "constants" of this module.

        :param symbol:
        :return: the values to be used by the rules engine. The genepanel can have gene specific values
         that will override the global defaults.
        """

        # init the result using the defaults. The result might be mutated further down.
        result = copy.deepcopy(self.genepanel_default)
        result.pop(KEY_CUTOFFS, None)  # cutoffs is handled specially below

        # find frequency cutoffs when we don't have any specific info:
        # start
        if not symbol:  # use non-AD cutoffs from either hardcoded or configured defaults. Relevant for tests only.
            logging.warning("Symbol not defined when resolving genepanel config values")
            result[KEY_CUTOFFS] = self.genepanel_default[KEY_CUTOFFS]['Other'] if self.genepanel_default else DEFAULT_CUTOFFS
            return copy.deepcopy(result)

        if not self.genepanel:  # no panel to find any specific info
            logging.warning("Genepanel not defined when resolving genepanel config values")
            result[KEY_CUTOFFS] = DEFAULT_CUTOFFS
            return copy.deepcopy(result)
        # end

        # replace defaults with overrides from the gene panel:
        if self.genepanel.config and 'data' in self.genepanel.config and symbol in self.genepanel.config['data']:
            gene_specific_overrides = self.genepanel.config['data'][symbol]
            result.update(gene_specific_overrides)

            # use inheritance to find cutoffs:
            if KEY_INHERITANCE in gene_specific_overrides:
                result[KEY_CUTOFFS] = copy.deepcopy(_find_cutoffs(gene_specific_overrides[KEY_INHERITANCE]))
            else:
                result[KEY_CUTOFFS] = copy.deepcopy(_find_cutoffs(self.genepanel.find_inheritance(symbol)))

            # the gene panel can have overrides for either lo/hi frequencies:
            if KEY_HI in gene_specific_overrides:
                result[KEY_CUTOFFS][KEY_HI] = gene_specific_overrides[KEY_HI]
            if KEY_LO in gene_specific_overrides:
                result[KEY_CUTOFFS][KEY_LO] = gene_specific_overrides[KEY_LO]

        else:
            result[KEY_CUTOFFS] = DEFAULT_CUTOFFS

        return copy.deepcopy(result)
