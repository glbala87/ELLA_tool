import logging
import copy

# Global config values that can be overridden by gene panels.
KEY_INHERITANCE = 'inheritance'
KEY_LO = "lo_freq_cutoff"
KEY_HI = "hi_freq_cutoff"
KEY_CUTOFFS = "freq_cutoffs"

# values defined in Excel file WebUI_config_rules
DEFAULT_CUTOFFS = {KEY_HI: 0.01, KEY_LO: 1.0}
AD_CUTOFFS = {KEY_HI: 0.0005, KEY_LO: 0.0001}

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
Reads the genepanel specific config and overrides the default values.
"""


def _find_cutoffs(inheritance_code):
    """

    :param inheritance_code:
    :return: a dict with lo and hi cutoffs
    """

    if not inheritance_code:
        return DEFAULT_CUTOFFS

    if isinstance(inheritance_code, list):
        codes = set(inheritance_code)
        if len(codes) > 1:
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
        :param genepanel_default: the default for all panels. If None use the hardcoded defaults
        """
        super(GenepanelConfigResolver, self).__init__()
        self.genepanel = genepanel
        self.genepanel_default = COMMON_GENEPANEL_CONFIG if not genepanel_default else genepanel_default

    def resolve(self, symbol):
        """
        Find the config values using any overrides that might be defined on the genepanel.

        Uses deepcopy to avoid any mutation of the "constants" of this module.

        :param symbol:
        :return: the values to be used by the rules engine. The genepanel can have gene specific values
         that will override the global defaults.
        """

        result = copy.deepcopy(self.genepanel_default)
        result.pop(KEY_CUTOFFS, None)  # cutoffs is handled specially below

        # resolve frequency cutoffs:
        if not symbol:  # relevant for tests only. In tests either symbol is undefined or the default config needs to be set
            logging.warn("Symbol not defined when resolving genepanel config values")
            result[KEY_CUTOFFS] = self.genepanel_default[KEY_CUTOFFS]['Other'] if self.genepanel_default else DEFAULT_CUTOFFS
            return copy.deepcopy(result)

        if not self.genepanel:
            logging.warn("Genepanel not defined when resolving genepanel config values")
            result[KEY_CUTOFFS] = DEFAULT_CUTOFFS
            return copy.deepcopy(result)

        if self.genepanel.config and 'data' in self.genepanel.config and symbol in self.genepanel.config['data']:
            gene_config = self.genepanel.config['data'][symbol]
            result.update(gene_config)

            # use inheritance to choose default set of cutoffs
            if KEY_INHERITANCE in gene_config:
                result[KEY_CUTOFFS] = copy.deepcopy(_find_cutoffs(gene_config[KEY_INHERITANCE]))
            else:
                result[KEY_CUTOFFS] = copy.deepcopy(_find_cutoffs(self.genepanel.find_inheritance(symbol)))

            if KEY_HI in gene_config:
                result[KEY_CUTOFFS][KEY_HI] = gene_config[KEY_HI]
            if KEY_LO in gene_config:
                result[KEY_CUTOFFS][KEY_LO] = gene_config[KEY_LO]

        else:
            result[KEY_CUTOFFS] = DEFAULT_CUTOFFS

        return copy.deepcopy(result)
