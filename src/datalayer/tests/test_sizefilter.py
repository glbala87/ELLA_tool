from datalayer.allelefilter.sizefilter import SizeFilter
from vardb.datamodel import allele
import hypothesis as ht
import hypothesis.strategies as st


@st.composite
def allele_sizes(draw):
    # allele_ids = draw(st.lists(elements=st.integers(min_value=1, max_value=10), unique=True))
    # N = len(allele_ids)
    # sizes = [draw(st.integers(min_value=1, max_value=100)) for _ in range(N)]
    sizes = draw(
        st.lists(elements=st.integers(min_value=1, max_value=100), min_size=1, max_size=10)
    )
    return sizes


@st.composite
def filter_config(draw):
    mode = draw(st.sampled_from([">", "<", ">=", "<=", "=="]))
    threshold = draw(st.integers(min_value=0, max_value=100))
    return {"mode": mode, "treshold": threshold}


@ht.given(st.one_of(allele_sizes()), st.one_of(filter_config()))
def test_sizefilter(session, allele_sizes, filter_config):

    # Apply sizes to some allele objects
    allele_objs = session.query(allele.Allele).limit(len(allele_sizes)).all()
    for obj, size in zip(allele_objs, allele_sizes):
        obj.length = size
    allele_ids = [obj.id for obj in allele_objs]
    session.flush()

    sf = SizeFilter(session, None)
    res = sf.filter_alleles({("Dabla", "v01"): allele_ids}, filter_config)

