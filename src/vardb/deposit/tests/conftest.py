from contextlib import contextmanager, nullcontext
from vardb.util.vcfiterator import VcfIterator, RESERVED_GT_HEADERS
import tempfile
import cyvcf2
import os
import pytest

VCF_HEADER_TEMPLATE = """##fileformat=VCFv4.1
#CHROM\tPOS\tID\tREF\tALT\tQUAL\tFILTER\tINFO\tFORMAT{SAMPLES}"""
VCF_LINE_TEMPLATE = "{CHROM}\t{POS}\t{ID}\t{REF}\t{ALT}\t{QUAL}\t{FILTER}\t{INFO}"


@pytest.mark.skip(reason="This is not a test, just a helper class")
class TestVcfWriter:
    def __init__(self):
        self.filename = tempfile.mktemp()
        self.writer = None
        self.samples = None

    @staticmethod
    def _get_header_for_info(k, v):
        def get_type(x):
            # Integer, Float, Flag, Character, and String.
            if isinstance(x, int):
                return "Integer"
            elif isinstance(x, float):
                return "Float"
            elif isinstance(x, bool):
                return "Flag"
            else:
                return "String"

        if isinstance(v, list):
            N = len(v)
            value_type = get_type(v[0])
            assert all(get_type(x) == value_type for x in v)
        else:
            N = 1
            value_type = get_type(v)

        return {"ID": k, "Type": value_type, "Description": "Added in test", "Number": N}

    def set_samples(self, samples):
        assert self.writer is None
        self.samples = samples

    def _init(self):
        if self.writer is not None:
            return
        vcf_header = VCF_HEADER_TEMPLATE.format(
            SAMPLES="" if not self.samples else "\t" + "\t".join(self.samples)
        )
        self.writer = cyvcf2.Writer.from_string(self.filename, vcf_header)
        for key, fmt in RESERVED_GT_HEADERS.items():
            self.writer.add_format_to_header({**fmt, **{"ID": key}})

    def _get_format_str(self, fmt):
        if not fmt:
            return ""
        else:

            assert self.samples is not None and len(self.samples) == len(fmt)
            format_keys = set(sum((list(x.keys()) for x in fmt), []))
            format_str = "\t" + ":".join(format_keys)
            for sample_format in fmt:
                format_str += "\t" + ":".join([str(sample_format.get(k, ".")) for k in format_keys])
            return format_str

    def _get_annotation_string(self, info):
        if not info:
            return "."
        else:
            annotation = []
            for k, v in info.items():
                self.writer.add_info_to_header(self._get_header_for_info(k, v))
                if isinstance(v, bool):
                    annotation.append(k)
                elif isinstance(v, (list, tuple)):
                    annotation.append(f"{k}={','.join(str(x) for x in v)}")
                else:
                    annotation.append(f"{k}={v}")
            return ";".join(annotation)

    def add_variant(self, variant_kwargs, fmt):
        self._init()
        # Fallback to default values
        variant_kwargs.setdefault("CHROM", "1")
        variant_kwargs.setdefault("POS", 123)
        variant_kwargs.setdefault("ID", ".")
        variant_kwargs.setdefault("REF", "A")
        variant_kwargs.setdefault("ALT", "C")
        variant_kwargs.setdefault("QUAL", ".")
        variant_kwargs.setdefault("FILTER", ".")
        variant_kwargs["INFO"] = self._get_annotation_string(variant_kwargs.get("INFO"))

        if variant_kwargs["FILTER"] not in [("PASS", ".")]:
            self.writer.add_filter_to_header(
                {"ID": variant_kwargs["FILTER"], "Description": "Added in test"}
            )

        variant_line = VCF_LINE_TEMPLATE.format(**variant_kwargs) + self._get_format_str(fmt)
        self.writer.add_to_header(f"##contig=<ID={variant_kwargs['CHROM']}>")

        v = self.writer.variant_from_string(variant_line)
        self.writer.write_record(v)

    def close(self):
        if self.writer:
            self.writer.close()

    def __enter__(self):
        return self

    def __exit__(self, *args, **kwargs):
        if self.writer:
            self.writer.close()
        if os.path.isfile(self.filename):
            os.unlink(self.filename)


def mock_record(variant, fmt=None, samples=None):
    with TestVcfWriter() as writer:

        writer.set_samples(samples)
        writer.add_variant(variant, fmt)
        writer.close()

        vi = VcfIterator(writer.filename)
        record = next(iter(vi))
    return record


@contextmanager
def tempinput(data: str):
    temp = tempfile.NamedTemporaryFile(delete=False)
    temp.write(data.encode())
    temp.close()
    try:
        yield temp.name
    finally:
        os.unlink(temp.name)


def ped_info_file(ped_info):
    if ped_info is None or len(ped_info) == 1:
        return nullcontext()

    PED_LINE = "{fam}\t{sample}\t{father}\t{mother}\t{sex}\t{affected}\t{proband}"
    ped_str = ""
    for ped_info in ped_info.values():
        ped_str += PED_LINE.format(**ped_info) + "\n"

    return tempinput(ped_str)
