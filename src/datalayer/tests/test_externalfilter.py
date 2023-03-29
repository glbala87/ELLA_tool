import operator
from datalayer.allelefilter.externalfilter import ExternalFilter, CLINVAR_CLINSIG_GROUPS
from api.config.config import config
from conftest import mock_allele_with_annotation

import hypothesis as ht
import hypothesis.strategies as st

OPERATORS = {
    "==": operator.eq,
    ">=": operator.ge,
    "<=": operator.le,
    ">": operator.gt,
    "<": operator.lt,
}


def create_external_annotation(
    draw, num_stars, num_benign, num_uncertain, num_pathogenic, hgmd_tag
):
    external_annotation = {}

    clinical_significance_status = {
        1: "criteria provided, conflicting interpretations",
        2: "criteria provided, multiple submitters, no conflicts",
        0: "no assertion criteria provided",
        4: "practice guideline",
        3: "reviewed by expert panel",
    }
    external_annotation["CLINVAR"] = {
        "variant_description": clinical_significance_status[num_stars],
        "items": [],
        "variant_id": 12345,
    }

    item_base = {
        "rcv": "",
        "traitnames": "",
        "clinical_significance_descr": "",
        "variant_id": "",
        "submitter": "",
        "last_evaluated": "",
    }

    def clinvar_clinsig_random_casing(draw, group):
        clnsig = draw(st.sampled_from(CLINVAR_CLINSIG_GROUPS[group]))
        uppercase_slices = draw(st.lists(st.integers(min_value=0, max_value=len(clnsig) - 1)))
        clnsig = "".join(
            [
                clnsig[i].upper() if i in uppercase_slices else clnsig[i].lower()
                for i in range(len(clnsig))
            ]
        )
        return clnsig

    for n in range(num_benign):
        item = dict(item_base)
        item.update(
            {
                "rcv": "SCVXXXXXXXX",
                "clinical_significance_descr": clinvar_clinsig_random_casing(draw, "benign"),
            }
        )
        external_annotation["CLINVAR"]["items"].append(item)

    for n in range(num_uncertain):
        item = dict(item_base)
        item.update(
            {
                "rcv": "SCVXXXXXXXX",
                "clinical_significance_descr": clinvar_clinsig_random_casing(draw, "uncertain"),
            }
        )
        external_annotation["CLINVAR"]["items"].append(item)

    for n in range(num_pathogenic):
        item = dict(item_base)
        item.update(
            {
                "rcv": "SCVXXXXXXXX",
                "clinical_significance_descr": clinvar_clinsig_random_casing(draw, "pathogenic"),
            }
        )
        external_annotation["CLINVAR"]["items"].append(item)

    if hgmd_tag:
        external_annotation["HGMD"] = {"tag": hgmd_tag, "acc_num": "dabla", "disease": "dabla"}

    if not external_annotation["CLINVAR"]["items"]:
        item = dict(item_base)
        item.update({"rcv": "SCVXXXXXXXX", "clinical_significance_descr": "something"})
        external_annotation["CLINVAR"]["items"].append(item)

    return {"external": external_annotation}


@st.composite
def external_annotation(draw):
    num_benign = draw(st.integers(min_value=0, max_value=5))
    num_uncertain = draw(st.integers(min_value=0, max_value=5))
    num_pathogenic = draw(st.integers(min_value=0, max_value=5))
    num_stars = draw(st.integers(min_value=0, max_value=4))
    hgmd_tag = draw(st.sampled_from([None, "FP", "DM", "DFP", "R", "DP", "DM?"]))

    meta_external_annotation = {
        "num_benign": num_benign,
        "num_uncertain": num_uncertain,
        "num_pathogenic": num_pathogenic,
        "num_stars": num_stars,
        "hgmd_tag": hgmd_tag,
    }
    external_annotation = create_external_annotation(draw, **meta_external_annotation)
    return meta_external_annotation, external_annotation


@st.composite
def clinvar_strategy(draw):
    ca = draw(st.sampled_from(["benign", "uncertain", "pathogenic"]))
    op = draw(st.sampled_from(["==", "<", "<=", ">", ">="]))
    cb = draw(st.sampled_from(["benign", "uncertain", "pathogenic"] + list(range(6))))
    ht.assume(ca != cb)
    ht.assume(not (op in ["<=", "<"] and cb == 0))

    return [ca, op, cb]


@st.composite
def clinvar_stars(draw):
    op = draw(st.sampled_from(["==", "<", "<=", ">", ">="]))
    num = draw(st.integers(min_value=0, max_value=4))
    ht.assume(not (op in ["<=", "<"] and num == 0))
    return [op, num]


@st.composite
def hgmd_strategy(draw):
    hgmd_tags = draw(
        st.lists(st.sampled_from([None, "FP", "DM", "DFP", "R", "DP", "DM?"]), unique=True)
    )
    return hgmd_tags


@ht.given(
    st.lists(external_annotation(), min_size=1, max_size=15),
    st.lists(clinvar_strategy(), max_size=3),
    st.one_of(clinvar_stars()),
    st.one_of(st.booleans()),
    st.one_of(hgmd_strategy()),
    st.one_of(st.booleans()),
)
@ht.settings(deadline=3000)
def test_externalfilter(
    session,
    external_annotations,
    clinvar_strategy,
    clinvar_stars,
    clinvar_inverse,
    hgmd_strategy,
    hgmd_inverse,
):
    allele_ids_annotations = []
    allele_ids = []
    for meta_annotation, annotation in external_annotations:
        al, _ = mock_allele_with_annotation(session, annotations=annotation)
        allele_ids_annotations.append((al.id, meta_annotation))
        allele_ids.append(al.id)

    filter_config = {}
    if clinvar_strategy or clinvar_stars:
        filter_config["clinvar"] = {}
        if clinvar_strategy:
            filter_config["clinvar"]["combinations"] = clinvar_strategy
        if clinvar_stars:
            filter_config["clinvar"]["num_stars"] = clinvar_stars
        if clinvar_inverse:
            filter_config["clinvar"]["inverse"] = clinvar_inverse

    if hgmd_strategy:
        filter_config["hgmd"] = {"tags": hgmd_strategy}
        if hgmd_inverse:
            filter_config["hgmd"]["inverse"] = hgmd_inverse

    testdata = {"key": allele_ids}

    # Compute clinvar result
    if clinvar_stars or clinvar_strategy:
        clinvar_result = []
        for allele_id, meta_annotation in allele_ids_annotations:
            if clinvar_stars:
                op, count = clinvar_stars
                if not OPERATORS[op](meta_annotation["num_stars"], count):
                    continue

            flag = False
            for c in clinvar_strategy:
                ca, op, cb = c
                ca = meta_annotation.get("num_" + str(ca), ca)
                cb = meta_annotation.get("num_" + str(cb), cb)
                if not OPERATORS[op](ca, cb):
                    flag = True
                    break
            if flag:
                continue

            clinvar_result.append(allele_id)

        if clinvar_inverse:
            clinvar_result = list(set(allele_ids) - set(clinvar_result))
    else:
        clinvar_result = allele_ids

    if hgmd_strategy:
        hgmd_result = []
        for allele_id, meta_annotation in allele_ids_annotations:
            if not meta_annotation["hgmd_tag"] in hgmd_strategy:
                continue
            hgmd_result.append(allele_id)

        if hgmd_inverse:
            hgmd_result = list(set(allele_ids) - set(hgmd_result))
    else:
        hgmd_result = allele_ids

    expected_result = {"key": set(clinvar_result) & set(hgmd_result)}

    ef = ExternalFilter(session, config)
    result = ef.filter_alleles(testdata, filter_config)
    assert expected_result == result
