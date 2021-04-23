from .clinvarjsonconverter import CLINVARJSONConverter
from .vepconverter import VEPConverter
from .keyvalueconverter import KeyValueConverter
from .jsonconverter import JSONConverter
from .references import HGMDExtraRefs, HGMDPrimaryReport, ClinVarReferences
from .hgmd import HGMDConverter

ANNOTATION_CONVERTERS = {
    "vep": VEPConverter,
    "json": JSONConverter,
    "keyvalue": KeyValueConverter,
    "hgmdextrarefs": HGMDExtraRefs,
    "hgmdprimaryreport": HGMDPrimaryReport,
    "clinvarreferences": ClinVarReferences,
    "hgmd": HGMDConverter,
    "clinvarjson": CLINVARJSONConverter,
}
