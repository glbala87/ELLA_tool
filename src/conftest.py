import os
import tempfile
from contextlib import contextmanager, nullcontext
from functools import partial, update_wrapper

import cyvcf2
import hypothesis as ht
import pytest

from api.tests.util import FlaskClientProxy
from vardb.datamodel import allele, annotation
from vardb.deposit.annotationconverters import AnnotationConverters
from vardb.util import DB
from vardb.util.testdatabase import TestDatabase
from vardb.util.vcfiterator import RESERVED_GT_HEADERS, VcfIterator

ht.settings.register_profile(
    "default", deadline=1000, suppress_health_check=(ht.HealthCheck.function_scoped_fixture,)
)
# allow disabling deadline for local dev testing
ht.settings.register_profile(
    "dev", deadline=None, suppress_health_check=(ht.HealthCheck.function_scoped_fixture,)
)
ht.settings.register_profile(
    "small", max_examples=20, suppress_health_check=(ht.HealthCheck.function_scoped_fixture,)
)
ht.settings.register_profile(
    "extensive",
    max_examples=3000,
    deadline=2000,
    suppress_health_check=(ht.HealthCheck.function_scoped_fixture,),
)
ht.settings.register_profile(
    "soak",
    max_examples=1_000_000,
    deadline=2000,
    suppress_health_check=(ht.HealthCheck.function_scoped_fixture,),
)

hypothesis_profile = os.environ.get("HYPOTHESIS_PROFILE", "default").lower()
ht.settings.load_profile(hypothesis_profile)


@pytest.yield_fixture
def session(request):
    db = DB()
    db.connect()
    session = db.session()

    yield session
    # Close session on teardown
    session.close()
    db.disconnect()


# Will be shared among all tests
@pytest.yield_fixture(scope="session", autouse=True)
def test_database(request):
    """
    The TestDatabase object is yielded in order for the user to
    be able to call refresh() when he wants a fresh database.
    """
    test_db = TestDatabase()
    test_db.refresh()
    yield test_db

    # Cleanup database on teardown
    test_db.cleanup()


@pytest.fixture
def client():
    """
    Fixture for a flask client proxy, that supports get, post etc.
    """
    return FlaskClientProxy()


allele_start = 0


def _create_annotation(annotations, allele=None, allele_id=None):
    annotations.setdefault("external", {})
    annotations.setdefault("frequencies", {})
    annotations.setdefault("prediction", {})
    annotations.setdefault("references", [])
    annotations.setdefault("transcripts", [])
    for t in annotations["transcripts"]:
        t.setdefault("consequences", [])
        t.setdefault("transcript", "NONE_DEFINED")
        t.setdefault("strand", 1)
        t.setdefault("is_canonical", True)
        t.setdefault("in_last_exon", "no")

    kwargs = {"annotations": annotations}
    if allele:
        kwargs["allele"] = allele
    elif allele_id:
        kwargs["allele_id"] = allele_id
    kwargs["annotation_config_id"] = 1
    return annotation.Annotation(**kwargs)


VCF_HEADER_TEMPLATE = """##fileformat=VCFv4.1
#CHROM\tPOS\tID\tREF\tALT\tQUAL\tFILTER\tINFO\tFORMAT{SAMPLES}"""
VCF_LINE_TEMPLATE = "{CHROM}\t{POS}\t{ID}\t{REF}\t{ALT}\t{QUAL}\t{FILTER}\t{INFO}"


class MockVcfWriter:
    def __init__(self):
        self.filename = tempfile.mktemp()
        self.writer = None
        self.samples = None

    @staticmethod
    def _get_header_for_info(k, v):
        def get_type(x):
            # Integer, Float, Flag, Character, and String.
            if isinstance(x, bool):
                return "Flag"
            elif isinstance(x, int):
                return "Integer"
            elif isinstance(x, float):
                return "Float"
            else:
                return "String"

        if isinstance(v, (list, tuple)):
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
                    if v:
                        annotation.append(k)
                    else:
                        continue
                elif isinstance(v, (list, tuple)):
                    annotation.append(f"{k}={','.join(str(x) for x in v)}")
                else:
                    annotation.append(f"{k}={v}")
            return ";".join(annotation)

    def add_variant(self, variant_kwargs, fmt):
        self._init()
        if variant_kwargs is None:
            variant_kwargs = {}
        global allele_start
        allele_start += 1
        # Fallback to default values
        variant_kwargs.setdefault("CHROM", "1")
        variant_kwargs.setdefault("POS", allele_start)
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


def mock_record(variant=None, fmt=None, samples=None):
    with MockVcfWriter() as writer:
        writer.set_samples(samples)
        writer.add_variant(variant, fmt)
        writer.close()

        vi = VcfIterator(writer.filename)
        record = next(iter(vi))
    return record


def mock_allele_with_annotation(session, allele_data=None, vcf_data=None, annotations=None):
    assert annotations is not None, "Create allele using mock_allele if no annotation is required"
    al = mock_allele(session, allele_data=allele_data, vcf_data=vcf_data)
    an = _create_annotation(annotations, allele_id=al.id)
    session.add(an)
    session.flush()
    return al, an


def mock_allele(session, allele_data=None, vcf_data=None):
    if allele_data is None:
        allele_data = {}
    complete_allele_data = {
        **mock_record(vcf_data).allele,
        **allele_data,
    }
    al = allele.Allele(**complete_allele_data)
    session.add(al)
    session.flush()
    return al


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


class ConverterConfig:
    """
    Shortcut class to create Config objects for all members of AnnotationConverters, which should
    be all of them.

    e.g., cc.vep(), cc.keyvalue(), ...
    """

    defaults = {
        "source": "test source",
        "target": "test target",
    }
    custom = {
        "clinvarjson": {"source": "CLINVARJSON"},
        "hgmdprimaryreport": {"source": "HGMD__pmid"},
        "vep": {"source": "CSQ"},
    }

    def __init__(self) -> None:
        # dynamically sets attributes based on member name, see class def for full list
        for ac in AnnotationConverters:
            default_args = {**self.defaults, **self.custom.get(ac.name, {})}
            setattr(
                self,
                ac.name,
                update_wrapper(partial(ac.value.Config, **default_args), ac.value.Config),
            )


cc = ConverterConfig()
