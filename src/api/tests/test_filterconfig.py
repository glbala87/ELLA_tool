import hypothesis as ht
import hypothesis.strategies as st
from api.util import queries
from vardb.datamodel import sample, gene, jsonschema
import string
import time


@st.composite
def filterconfig_strategy(draw):
    req_strategy = [
        (st.just("is_trio"), st.booleans()),
        (st.just("is_family"), st.booleans()),
        (st.just("is_single"), st.booleans()),
        (st.just("name"), st.just(".*brca.*")),
    ]
    fc_strategy = {
        "order": st.integers(min_value=0, max_value=10000),
        "usergroup_id": st.sampled_from([1, 2]),
        "active": st.booleans(),
        "name": st.text(alphabet=string.ascii_letters, min_size=8),
        "filterconfig": st.just({}),
    }

    num_configs = draw(st.integers(min_value=1, max_value=10))
    filterconfigs = []
    for i in range(num_configs):
        fc = draw(st.fixed_dictionaries(fc_strategy))

        has_requirements = draw(st.booleans())
        if has_requirements:
            reqs = draw(st.lists(st.sampled_from(req_strategy), min_size=1))
            reqs = dict((draw(k), draw(v)) for k, v in reqs)
            requirements = [{"function": "analysis", "params": reqs}]
        else:
            requirements = []

        fc["requirements"] = requirements
        filterconfigs.append(fc)

    # Check name, usergroup_id, active=True is unique
    active_fc = [fc for fc in filterconfigs if fc["active"]]
    ht.assume(len(set((fc["name"], fc["usergroup_id"]) for fc in active_fc)) == len(active_fc))

    # # Check usergroup_id, order, active=True is unique
    ht.assume(len(set((fc["usergroup_id"], fc["order"]) for fc in active_fc)) == len(active_fc))

    # Check that usergroup_id has at least one active filterconfig without requirements
    no_reqs = [fc for fc in active_fc if fc["requirements"] == []]
    ht.assume(len(set([fc["usergroup_id"] for fc in no_reqs])) == 2)
    return filterconfigs


def create_dummy_analysis(session):
    # Create a dummy trio analysis, to test filter config requirements
    try:
        # Check if analysis already created. If so, return this
        return session.query(sample.Analysis).filter(sample.Analysis.name == "TrioDummy").one()
    except:
        pass

    an = sample.Analysis(name="TrioDummy")
    session.add(an)
    session.flush()

    common = {"family_id": "DummyFamily", "analysis_id": an.id, "sample_type": "HTS"}

    mother = sample.Sample(
        proband=False, affected=False, sex="Female", identifier="DummyMother", **common
    )
    father = sample.Sample(
        proband=False, affected=False, sex="Male", identifier="DummyFather", **common
    )
    session.add_all([mother, father])
    session.flush()

    proband = sample.Sample(
        proband=True,
        affected=True,
        mother_id=mother.id,
        father_id=father.id,
        identifier="DummyProband",
        **common,
    )
    session.add(proband)
    session.flush()
    return an


@ht.given(st.one_of(filterconfig_strategy()))
@ht.settings(suppress_health_check=(ht.HealthCheck.too_slow,))
def test_filter_ordering(session, client, filterconfigs):
    session.rollback()
    session.query(sample.FilterConfig).delete()

    # Add dummy schema that allows for any object
    jsonschema.JSONSchema.get_or_create(
        session, **{"name": "filterconfig", "version": 1000, "schema": {"type": "object"}}
    )
    session.add_all([sample.FilterConfig(**fc) for fc in filterconfigs])
    session.commit()

    r = client.get("/api/v1/workflows/analyses/{}/filterconfigs/".format(1))

    assert r.status_code == 200
    returned_fc = r.get_json()
    assert len(returned_fc) > 0

    # Check that returned results are sorted on order
    assert [fc["order"] for fc in returned_fc] == sorted([fc["order"] for fc in returned_fc])


@ht.given(st.one_of(filterconfig_strategy()))
@ht.settings(suppress_health_check=(ht.HealthCheck.too_slow,))
def test_filterconfig_requirements(session, client, filterconfigs):
    an = create_dummy_analysis(session)
    session.query(sample.FilterConfig).delete()
    filterconfigs = [sample.FilterConfig(**fc) for fc in filterconfigs]
    session.add_all(filterconfigs)
    session.commit()

    r = client.get("/api/v1/workflows/analyses/{}/filterconfigs/".format(an.id))
    assert r.status_code == 200
    returned_fc = r.get_json()
    returned_fc_ids = [fc["id"] for fc in returned_fc]

    usergroup = 1

    expected_fc_ids = []
    for fc in filterconfigs:
        if fc.usergroup_id != usergroup:
            continue

        if not fc.active:
            continue
        if not fc.requirements:
            expected_fc_ids.append(fc.id)
        else:
            if fc.requirements[0]["params"].get("is_trio") == False:
                continue
            if fc.requirements[0]["params"].get("is_family") == False:
                continue
            if fc.requirements[0]["params"].get("is_single") == True:
                continue
            if fc.requirements[0]["params"].get("name"):
                continue
            expected_fc_ids.append(fc.id)

    assert set(expected_fc_ids) == set(returned_fc_ids)

    r = client.get("/api/v1/workflows/analyses/{}/filterconfigs/".format(1))
    assert r.status_code == 200
    returned_fc = r.get_json()
    returned_fc_ids = [fc["id"] for fc in returned_fc]

    expected_fc_ids = []
    for fc in filterconfigs:
        if fc.usergroup_id != usergroup:
            continue

        if not fc.active:
            continue
        if not fc.requirements:
            expected_fc_ids.append(fc.id)
        else:
            if fc.requirements[0]["params"].get("is_trio") == True:
                continue
            if fc.requirements[0]["params"].get("is_family") == True:
                continue
            if fc.requirements[0]["params"].get("is_single") == False:
                continue
            expected_fc_ids.append(fc.id)

    assert set(expected_fc_ids) == set(returned_fc_ids)


@ht.given(st.one_of(filterconfig_strategy()))
@ht.settings(suppress_health_check=(ht.HealthCheck.too_slow,))
def test_default_filterconfig(session, filterconfigs):
    session.rollback()
    session.query(sample.FilterConfig).delete()
    session.add_all([sample.FilterConfig(**fc) for fc in filterconfigs])
    session.commit()

    returned_fc = queries.get_valid_filter_configs(session, 1, analysis_id=None).all()
    assert all([fc.requirements == [] for fc in returned_fc])
