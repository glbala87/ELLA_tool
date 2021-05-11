from vardb.deposit.annotationconverters.metaconverter import MetaConverter
from vardb.deposit.annotationconverters.clinvarjsonconverter import CLINVARJSONConverter
from vardb.deposit.annotationconverters.vepconverter import VEPConverter
from vardb.deposit.annotationconverters.keyvalueconverter import KeyValueConverter
from vardb.deposit.annotationconverters.jsonconverter import JSONConverter
from vardb.deposit.annotationconverters.references import (
    HGMDExtraRefs,
    HGMDPrimaryReport,
    ClinVarReferences,
)
from vardb.deposit.annotationconverters.hgmd import HGMDConverter
from vardb.deposit.annotationconverters.flatjsonconverter import FlatJSONConverter

ANNOTATION_CONVERTERS = {
    "vep": VEPConverter,
    "json": JSONConverter,
    "keyvalue": KeyValueConverter,
    "hgmdextrarefs": HGMDExtraRefs,
    "hgmdprimaryreport": HGMDPrimaryReport,
    "clinvarreferences": ClinVarReferences,
    "hgmd": HGMDConverter,
    "clinvarjson": CLINVARJSONConverter,
    "meta": MetaConverter,
    "flatjson": FlatJSONConverter,
}
