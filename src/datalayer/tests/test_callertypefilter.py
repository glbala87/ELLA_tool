from datalayer.allelefilter.callertypefilter import CallerTypeFilter
from vardb.datamodel import allele
import hypothesis as ht
import hypothesis.strategies as st


@st.composite
def allele_caller_types(draw):
    callerTypes = draw(st.lists(elements=st.sampled_from(["cnv", "snv"]), unique=True))
    return callerTypes


@st.composite
def filter_config(draw):
    modes = draw(st.lists(st.sampled_from(["cnv", "snv"]), unique=True))
    callerTypes = [{"callerTypes": [x]} for x in modes]
    return callerTypes


@ht.given(st.one_of(allele_caller_types()), st.one_of(filter_config()))
def test_callertypefilter(session, allele_caller_types, filter_config):

    # Apply sizes to some allele objects
    # We can filter on callertypes, extracting only the exact callerType
    # Then we can do filtering on all filter_configs, check that they
    # are exclusive, hence, one should contain all, and the other none in result
    allele_objs = session.query(allele.Allele).limit(len(allele_caller_types)).all()

    allele_ids = [obj.id for obj in allele_objs]
    session.flush()

    ctf = CallerTypeFilter(session, None)
    cfgKey = ("dummyname", "v01.0")
    testdata = {cfgKey: allele_ids}

    for callertypeFilter in filter_config:

        callerType = callertypeFilter["callerTypes"]

        localCheck = [obj for obj in allele_objs if obj.caller_type == callerType[0]]

        result = ctf.filter_alleles(testdata, callertypeFilter)
        assert len(localCheck) == len(result[cfgKey])
        assert len(result[cfgKey]) <= len(result[cfgKey])
