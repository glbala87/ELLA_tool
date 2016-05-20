import logging

# Global config values that can be overridden by gene panels.
KEY_INHERITANCE = 'inheritance'
KEY_LO = "lo_freq_cutoff"
KEY_HI = "hi_freq_cutoff"
KEY_CUTOFFS = "freq_cutoffs"

DEFAULT_CUTOFFS = {KEY_HI: 0.01, KEY_LO: 1.0}
# DEFAULT_CUTOFFS = {KEY_HI: 0.01, KEY_LO: 0.001}
AD_CUTOFFS = {KEY_HI: 0.0005, KEY_LO: 0.0001}

COMMON_GENEPANEL_CONFIG = {
    KEY_CUTOFFS: {
        "AD": AD_CUTOFFS,
        "Other": DEFAULT_CUTOFFS
    },
    KEY_INHERITANCE: "AD",
    "disease_mode": "ANY",
    "in_last_exon": True,
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

        genepanel_annotations = dict(self.genepanel_default)
        genepanel_annotations.pop(KEY_CUTOFFS, None)  # cutoffs is handled specially below

        # resolve frequency cutoffs:
        if not symbol:  # for tests where either symbol is undefined or the default config needs to be set
            logging.warn("Symbol not defined when resolving genepanel config values")
            genepanel_annotations[KEY_CUTOFFS] = self.genepanel_default[KEY_CUTOFFS]['Other'] if self.genepanel_default else DEFAULT_CUTOFFS
            return genepanel_annotations

        if not self.genepanel:
            logging.warn("Genepanel not defined when resolving genepanel config values")
            genepanel_annotations[KEY_CUTOFFS] = DEFAULT_CUTOFFS
            return genepanel_annotations

        if self.genepanel.config and symbol in self.genepanel.config:
            genepanel_config = self.genepanel.config[symbol]
            genepanel_annotations.update(genepanel_config)
            if KEY_CUTOFFS in genepanel_config:
                genepanel_annotations[KEY_CUTOFFS] = genepanel_config[KEY_CUTOFFS]
            else:  # use inheritance to choose set of cutoffs
                if KEY_INHERITANCE in genepanel_config:
                    genepanel_annotations[KEY_CUTOFFS] = _find_cutoffs(genepanel_config[KEY_INHERITANCE])
                else:
                    genepanel_annotations[KEY_CUTOFFS] = _find_cutoffs(self.genepanel.find_inheritance(symbol))
        else:
            genepanel_annotations[KEY_CUTOFFS] = DEFAULT_CUTOFFS

        return genepanel_annotations
