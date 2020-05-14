import hypothesis as ht
import hypothesis.strategies as st
from datalayer import queries
from vardb.datamodel import sample, jsonschema
import string


@st.composite
def filterconfig_strategy(draw):
    req_strategy = [
        (st.just("is_trio"), st.booleans()),
        (st.just("is_family"), st.booleans()),
        (st.just("is_single"), st.booleans()),
        (st.just("name"), st.just(".*brca.*")),
    ]
    fc_strategy = {
        "active": st.booleans(),
        "name": st.text(alphabet=string.ascii_letters, min_size=8),
        "filterconfig": st.just({}),
    }

    ugfc_strategy = {
        "order": st.integers(min_value=0, max_value=10000),
        "usergroup_id": st.sampled_from([1, 2]),
    }

    num_configs = draw(st.integers(min_value=1, max_value=10))
    filterconfigs = []
    for i in range(num_configs):
        fc = draw(st.fixed_dictionaries(fc_strategy))
        ugfc = draw(st.fixed_dictionaries(ugfc_strategy))

        has_requirements = draw(st.booleans())
        if has_requirements:
            reqs = draw(st.lists(st.sampled_from(req_strategy), min_size=1))
            reqs = dict((draw(k), draw(v)) for k, v in reqs)
            requirements = [{"function": "analysis", "params": reqs}]
        else:
            requirements = []

        fc["requirements"] = requirements
        filterconfigs.append((fc, ugfc))

    # Check name, usergroup_id, active=True is unique
    ht.assume(len(set(fc["name"] for fc, _ in filterconfigs)) == len(filterconfigs))

    # Check usergroup_id, order, active=True is unique
    active_fc = [(fc, ugfc) for fc, ugfc in filterconfigs if fc["active"]]
    ht.assume(
        len(set((ugfc["usergroup_id"], ugfc["order"]) for _, ugfc in active_fc)) == len(active_fc)
    )

    # Check that usergroup_id has at least one active filterconfig without requirements
    no_reqs = [ugfc for fc, ugfc in active_fc if fc["requirements"] == []]
    ht.assume(len(set([ugfc["usergroup_id"] for ugfc in no_reqs])) == 2)
    return filterconfigs


def create_dummy_trio_analysis(session):
    "Create a dummy trio analysis, to test filter config requirements"
    # Check if analysis already created. If so, return this
    an = session.query(sample.Analysis).filter(sample.Analysis.name == "TrioDummy").one_or_none()
    if an is not None:
        return an

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


def add_fcs_to_db(session, filterconfigs):
    "Create database objects from the hypothesis generated cases"
    filterconfigs_db = []
    for fc, ugfc in filterconfigs:
        fc_obj = sample.FilterConfig(**fc)
        session.add(fc_obj)
        session.flush()
        ugfc["filterconfig_id"] = fc_obj.id
        ugfc_obj = sample.UserGroupFilterConfig(**ugfc)
        session.add(ugfc_obj)
        session.flush()
        filterconfigs_db.append((fc_obj, ugfc_obj))
    return filterconfigs_db


@ht.given(st.one_of(filterconfig_strategy()))
@ht.settings(suppress_health_check=(ht.HealthCheck.too_slow,))
def test_filter_ordering(session, client, filterconfigs):
    session.rollback()
    session.query(sample.UserGroupFilterConfig).delete()
    session.query(sample.FilterConfig).delete()

    # Add dummy schema that allows for any object
    jsonschema.JSONSchema.get_or_create(
        session, **{"name": "filterconfig", "version": 1000, "schema": {"type": "object"}}
    )

    filterconfigs = add_fcs_to_db(session, filterconfigs)

    # session.add_all([sample.FilterConfig(**fc) for fc in filterconfigs])
    session.commit()

    r = client.get("/api/v1/workflows/analyses/{}/filterconfigs/".format(1))

    assert r.status_code == 200
    returned_fc = r.get_json()
    assert len(returned_fc) > 0

    # Check that returned results are sorted on order
    returned_fc_ids = [fc["id"] for fc in returned_fc]
    ugfc_sorted = sorted(
        [ugfc for _, ugfc in filterconfigs if ugfc.filterconfig_id in returned_fc_ids],
        key=lambda x: x.order,
    )
    assert returned_fc_ids == [ugfc.filterconfig_id for ugfc in ugfc_sorted]


@ht.given(st.one_of(filterconfig_strategy()))
@ht.settings(suppress_health_check=(ht.HealthCheck.too_slow,))
def test_filterconfig_requirements(session, client, filterconfigs):
    # Add dummy schema that allows for any object
    jsonschema.JSONSchema.get_or_create(
        session, **{"name": "filterconfig", "version": 1000, "schema": {"type": "object"}}
    )

    usergroup = 1

    # Test trio requirements
    analysis_id = create_dummy_trio_analysis(session).id
    session.query(sample.UserGroupFilterConfig).delete()
    session.query(sample.FilterConfig).delete()
    filterconfigs = add_fcs_to_db(session, filterconfigs)
    session.commit()

    r = client.get("/api/v1/workflows/analyses/{}/filterconfigs/".format(analysis_id))
    assert r.status_code == 200
    returned_fc = r.get_json()
    returned_fc_ids = [fc["id"] for fc in returned_fc]

    expected_fc_ids = []
    for fc, ugfc in filterconfigs:
        if ugfc.usergroup_id != usergroup:
            continue

        if not fc.active:
            continue
        if not fc.requirements:
            expected_fc_ids.append(fc.id)
        else:
            # Check that requirements satisfy a trio analysis
            if fc.requirements[0]["params"].get("is_trio") is False:
                continue
            if fc.requirements[0]["params"].get("is_family") is False:
                continue
            if fc.requirements[0]["params"].get("is_single") is True:
                continue
            if fc.requirements[0]["params"].get("name"):
                continue
            expected_fc_ids.append(fc.id)

    assert set(expected_fc_ids) == set(returned_fc_ids)

    # Test requirements with a single analysis (take analysis id 1)
    analysis_id = 1
    r = client.get("/api/v1/workflows/analyses/{}/filterconfigs/".format(analysis_id))
    assert r.status_code == 200
    returned_fc = r.get_json()
    returned_fc_ids = [fc["id"] for fc in returned_fc]

    expected_fc_ids = []
    for fc, ugfc in filterconfigs:
        if ugfc.usergroup_id != usergroup:
            continue

        if not fc.active:
            continue
        if not fc.requirements:
            expected_fc_ids.append(fc.id)
        else:
            # Check that requirements satisfy the single analysis
            if fc.requirements[0]["params"].get("is_trio") is True:
                continue
            if fc.requirements[0]["params"].get("is_family") is True:
                continue
            if fc.requirements[0]["params"].get("is_single") is False:
                continue
            expected_fc_ids.append(fc.id)

    assert set(expected_fc_ids) == set(returned_fc_ids)


@ht.given(st.one_of(filterconfig_strategy()))
@ht.settings(suppress_health_check=(ht.HealthCheck.too_slow,))
def test_default_filterconfig(session, filterconfigs):
    session.rollback()
    # Add dummy schema that allows for any object
    jsonschema.JSONSchema.get_or_create(
        session, **{"name": "filterconfig", "version": 1000, "schema": {"type": "object"}}
    )
    session.query(sample.UserGroupFilterConfig).delete()
    session.query(sample.FilterConfig).delete()
    filterconfigs = add_fcs_to_db(session, filterconfigs)
    session.commit()

    usergroup_id = 1
    returned_fc = queries.get_valid_filter_configs(session, usergroup_id, analysis_id=None).all()

    expected_fc_ids = []
    usergroup_active_fcs = [
        fc for (fc, ugfc) in filterconfigs if ugfc.usergroup_id == usergroup_id and fc.active
    ]

    # If only one active filter config, should return this
    # Otherwise, should only return the filterconfigs without requirements
    if len(usergroup_active_fcs) == 1:
        expected_fc_ids = [usergroup_active_fcs[0].id]
    else:
        expected_fc_ids = [fc.id for fc in usergroup_active_fcs if not fc.requirements]

    assert set([fc.id for fc in returned_fc]) == set(expected_fc_ids)
