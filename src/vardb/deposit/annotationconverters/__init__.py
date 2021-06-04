from enum import Enum
from typing import List, Sequence, TypeVar

from vardb.deposit.annotationconverters.annotationconverter import (
    AnnotationConverter,
    ConverterArgs,
    Primitives,
    TypeConverter,
)
from vardb.deposit.annotationconverters.clinvarjsonconverter import CLINVARJSONConverter
from vardb.deposit.annotationconverters.hgmdconverter import HGMDConverter
from vardb.deposit.annotationconverters.jsonconverter import JSONConverter
from vardb.deposit.annotationconverters.keyvalueconverter import KeyValueConverter
from vardb.deposit.annotationconverters.mappingconverter import MappingConverter
from vardb.deposit.annotationconverters.metaconverter import MetaConverter
from vardb.deposit.annotationconverters.referenceconverters import (
    ClinVarReferencesConverter,
    HGMDExtraRefsConverter,
    HGMDPrimaryReportConverter,
)
from vardb.deposit.annotationconverters.vepconverter import VEPConverter


class AnnotationConverters(Enum):
    # Generic converters
    json = JSONConverter
    keyvalue = KeyValueConverter
    meta = MetaConverter
    mapping = MappingConverter
    # Specific converters
    vep = VEPConverter
    clinvarjson = CLINVARJSONConverter
    hgmd = HGMDConverter
    hgmdextrarefs = HGMDExtraRefsConverter
    hgmdprimaryreport = HGMDPrimaryReportConverter
    clinvarreferences = ClinVarReferencesConverter

    @classmethod
    def keys(cls) -> List[str]:
        return [ac.name for ac in cls]

    @classmethod
    def values(cls) -> Sequence[AnnotationConverter]:
        return [ac.value for ac in cls]
