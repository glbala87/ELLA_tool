from datalayer.allelefilter.sizefilter import SizeFilter
from vardb.datamodel import allele
import hypothesis as ht
import hypothesis.strategies as st


@st.composite
def allele_sizes(draw):
    sizes = draw(
        st.lists(elements=st.integers(min_value=1, max_value=10000000), min_size=1, max_size=10)
    )
    return sizes


@st.composite
def filter_config(draw):
    mode = draw(st.sampled_from([">", "<", ">=", "<=", "=="]))
    threshold = draw(st.integers(min_value=0, max_value=10000000))
    return {"mode": mode, "threshold": threshold}


def local_sizefilter_impl(config, alleles):
    filtered_alleles = []

    for a in alleles:
        if config["mode"] == ">":
            if a.length > int(config["threshold"]):
                filtered_alleles.append(a.id)
        elif config["mode"] == "<":
            if a.length < int(config["threshold"]):
                filtered_alleles.append(a.id)
        elif config["mode"] == ">=":
            if a.length >= int(config["threshold"]):
                filtered_alleles.append(a.id)
        elif config["mode"] == "<=":
            if a.length <= int(config["threshold"]):
                filtered_alleles.append(a.id)
        elif config["mode"] == "==":
            if a.length == config["threshold"]:
                filtered_alleles.append(a.id)

        else:
            raise RuntimeError(f"filter config mode {config.mode} is not supported")

    return filtered_alleles


@ht.given(st.one_of(allele_sizes()), st.one_of(filter_config()))
def test_sizefilter(session, allele_sizes, filter_config):

    allele_objs = session.query(allele.Allele).limit(len(allele_sizes)).all()
    for obj, size in zip(allele_objs, allele_sizes):
        obj.length = size
    allele_ids = [obj.id for obj in allele_objs]
    session.flush()
    local_filtered = local_sizefilter_impl(filter_config, allele_objs)

    sf = SizeFilter(session, None)
    db_filtered = sf.filter_alleles({("Dabla", "v01.0"): allele_ids}, filter_config)
    assert sorted(list(db_filtered[("Dabla", "v01.0")])) == sorted(local_filtered)
