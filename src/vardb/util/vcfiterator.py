import cyvcf2
import logging
import numpy as np

log = logging.getLogger(__name__)


def _numpy_unknown_to_none(a):
    """
    Unknown values ('.') in integer arrays are assigned as '-inf' (e.g. for in32 the value is -2^31)
    Convert array to list, and replace these values with None
    """
    b = a.tolist()
    n = max(a.shape)
    indices = zip(*np.where(a < np.iinfo(a.dtype).min + n))

    def set_value(x, i, value):
        "Set value in nested lists"
        if len(i) > 1:
            x = set_value(x[i[0]], i[1:], value)
        else:
            x[i[0]] = value

    for idx in indices:
        set_value(b, idx, None)

    return b


def numpy_to_list(a):
    if a is None:
        return None
    if np.issubdtype(a.dtype, np.integer):
        return _numpy_unknown_to_none(a)
    else:
        return a.tolist()


class Record(object):
    def __init__(self, variant, samples, meta):
        self.variant = variant
        self.samples = samples
        self.meta = meta

    def _sample_index(self, sample_name):
        return self.samples.index(sample_name)

    def get_raw_filter(self):
        """Need to implement this here, as cyvcf2 does not distinguish between 'PASS' and '.' (both return None).
        Therefore, we need to parse the VCF line to get the raw filter status."""
        return str(self.variant).split("\t")[6]

    def sample_genotype(self, sample_name):
        return tuple(self.variant.genotypes[self._sample_index(sample_name)][:-1])

    def has_allele(self, sample_name):
        gt = self.sample_genotype(sample_name)
        return max(gt) == 1

    def get_format_sample(self, property, sample_name, scalar=False):
        if property == "GT":
            return self.sample_genotype(sample_name)
        else:
            prop = self.variant.format(property)
            if prop is not None:
                ret = numpy_to_list(prop[self._sample_index(sample_name)])
                if scalar:
                    assert len(ret) == 1
                    return ret[0]
                else:
                    return ret

    def get_format(self, property):
        if property == "GT":
            return self.variant.genotypes
        else:
            return numpy_to_list(self.variant.format(property))

    def get_block_id(self):
        return self.variant.INFO.get("OLD_MULTIALLELIC")

    def is_multiallelic(self):
        return self.get_block_id() is not None

    def is_sample_multiallelic(self, sample_name):
        return self.is_multiallelic() and bool(set(self.sample_genotype(sample_name)) - set([0, 1]))

    def annotation(self):
        return dict(x for x in self.variant.INFO)

    def __str__(self):
        s = repr(self.variant)

        if self.samples:
            genotypes = []
            for i, x in enumerate(self.variant.gt_bases):
                genotypes.append(f"{x} ({str(self.samples[i])})")

            s += f" - Genotypes: {', '.join(genotypes)}"
        return s


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
    def __init__(self, path_or_fileobject, include_raw=False):
        self.path_or_fileobject = path_or_fileobject
        self.reader = cyvcf2.Reader(self.path_or_fileobject, gts012=True)
        self.include_raw = include_raw
        self.samples = self.reader.samples
        self.add_format_headers()
        self.meta = {}
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
        if self.include_raw:
            for variant in self.reader:
                yield str(variant), variant
        else:
            for variant in self.reader:
                r = Record(variant, self.samples, self.meta)
                yield r
