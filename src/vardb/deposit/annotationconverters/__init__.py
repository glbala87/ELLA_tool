from vardb.deposit.annotationconverters.metaconverter import MetaConverter
from vardb.deposit.annotationconverters.clinvarjsonconverter import CLINVARJSONConverter
from vardb.deposit.annotationconverters.vepconverter import VEPConverter
from vardb.deposit.annotationconverters.keyvalueconverter import KeyValueConverter
from vardb.deposit.annotationconverters.jsonconverter import JSONConverter
from vardb.deposit.annotationconverters.referenceconverters import (
    HGMDExtraRefsConverter,
    HGMDPrimaryReportConverter,
    ClinVarReferencesConverter,
)
from vardb.deposit.annotationconverters.hgmd import HGMDConverter
from vardb.deposit.annotationconverters.mappingconverter import MappingConverter

ANNOTATION_CONVERTERS = {
    # Generic converters
    "json": JSONConverter,
    "keyvalue": KeyValueConverter,
    "meta": MetaConverter,
    "mapping": MappingConverter,
    # Specific converters
    "vep": VEPConverter,
    "clinvarjson": CLINVARJSONConverter,
    "hgmd": HGMDConverter,
    "hgmdextrarefs": HGMDExtraRefsConverter,
    "hgmdprimaryreport": HGMDPrimaryReportConverter,
    "clinvarreferences": ClinVarReferencesConverter,
}
