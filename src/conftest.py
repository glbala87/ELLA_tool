import os
import pytest
import hypothesis as ht
from api.tests.util import FlaskClientProxy
from vardb.util.testdatabase import TestDatabase
from vardb.util import DB
from vardb.datamodel import allele, annotation
from vardb.deposit.importers import build_allele_from_record

ht.settings.register_profile("default")
ht.settings.register_profile("small", max_examples=20)
ht.settings.register_profile(
    "extensive",
    max_examples=3000,
    timeout=900,
    suppress_health_check=[ht.HealthCheck.hung_test],
    deadline=2000,
)
ht.settings.register_profile(
    "soak",
    max_examples=1000000,
    timeout=ht.unlimited,
    suppress_health_check=[ht.HealthCheck.hung_test],
    deadline=2000,
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


allele_start = 1300


def create_allele(data=None):
    global allele_start
    record = {"CHROM": "1", "POS": allele_start, "REF": "A", "ALT": ["T"]}
    allele_start += 1

    if data:
        for k in data:
            assert k in record
            record[k] = data[k]

    item = build_allele_from_record(record, "GRCh37")

    return allele.Allele(**item)


def create_annotation(annotations, allele=None, allele_id=None):
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
    return annotation.Annotation(**kwargs)


def create_allele_with_annotation(session, annotations=None, allele_data=None):
    al = create_allele(data=allele_data)
    session.add(al)
    if annotations is not None:
        an = create_annotation(annotations, allele=al)
        session.add(an)
    else:
        an = None

    return al, an
