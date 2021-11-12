from typing import Dict, IO, Union
import cyvcf2
import logging
from vardb.util.vcfrecord import VCFRecord

log = logging.getLogger(__name__)


RESERVED_GT_HEADERS = {
    "AD": {"Number": "R", "Type": "Integer", "Description": "Injected. Read depth for each allele"},
    "ADF": {
        "Number": "R",
        "Type": "Integer",
        "Description": "Injected. Read depth for each allele on the forward strand",
    },
    "ADR": {
        "Number": "R",
        "Type": "Integer",
        "Description": "Injected. Read depth for each allele on the reverse strand",
    },
    "DP": {"Number": "1", "Type": "Integer", "Description": "Injected. Read depth"},
    "EC": {
        "Number": "A",
        "Type": "Integer",
        "Description": "Injected. Expected alternate allele counts",
    },
    "FT": {
        "Number": "1",
        "Type": "String",
        "Description": "Injected. Filter indicating if this genotype was “called”",
    },
    "GL": {"Number": "G", "Type": "Float", "Description": "Injected. Genotype likelihoods"},
    "GP": {
        "Number": "G",
        "Type": "Float",
        "Description": "Injected. Genotype posterior probabilities",
    },
    "GQ": {
        "Number": "1",
        "Type": "Integer",
        "Description": "Injected. Conditional genotype quality",
    },
    "GT": {"Number": "1", "Type": "String", "Description": "Injected. Genotype"},
    "HQ": {"Number": "2", "Type": "Integer", "Description": "Injected. Haplotype quality"},
    "MQ": {"Number": "1", "Type": "Integer", "Description": "Injected. RMS mapping quality"},
    "PL": {
        "Number": "G",
        "Type": "Integer",
        "Description": "Injected. Phred-scaled genotype likelihoods rounded to the closest integer",
    },
    "PP": {
        "Number": "G",
        "Type": "Integer",
        "Description": "Injected. Phred-scaled genotype posterior probabilities rounded to the closest integer",
    },
    "PQ": {"Number": "1", "Type": "Integer", "Description": "Injected. Phasing quality"},
    "PS": {"Number": "1", "Type": "Integer", "Description": "Injected. Phase"},
}


class VcfIterator(object):
    def __init__(self, path_or_fileobject: Union[str, IO], include_raw: bool = False):
        self.path_or_fileobject = path_or_fileobject
        self.reader = cyvcf2.Reader(self.path_or_fileobject, gts012=True)
        self.include_raw = include_raw
        self.samples = self.reader.samples
        self.add_format_headers()
        self.meta: Dict[str, list] = {}
        for h in self.reader.header_iter():
            if h.type not in self.meta:
                self.meta[h.type] = []
            self.meta[h.type].append(h.info())

    def add_format_headers(self):
        "Add format headers if they do not exist. This is a subset of the reserved genotype keys from https://samtools.github.io/hts-specs/VCFv4.3.pdf (table 2)"
        for key, fmt in RESERVED_GT_HEADERS.items():
            if key in self.reader and self.reader.get_header_type(key) == "FORMAT":
                existing_header_line = self.reader[key]
                if (
                    existing_header_line["Number"] != fmt["Number"]
                    or existing_header_line["Type"] != fmt["Type"]
                ):
                    log.warning(
                        f"Header for format field {key} in VCF does not match VCF spec. Ignoring."
                    )
            else:
                self.reader.add_format_to_header({**fmt, **{"ID": key}})

    def __iter__(self):
        variant: cyvcf2.Variant
        if self.include_raw:
            for variant in self.reader:
                yield str(variant), variant
        else:
            for variant in self.reader:
                r = VCFRecord(variant, self.samples, self.meta)
                yield r
