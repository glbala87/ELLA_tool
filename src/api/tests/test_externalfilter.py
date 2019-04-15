import pytest
import operator
import datetime
import pytz
from api.allelefilter.externalfilter import ExternalFilter
from api.config.config import config
from vardb.datamodel import annotation

import hypothesis as ht
import hypothesis.strategies as st

OPERATORS = {
    "==": operator.eq,
    ">=": operator.ge,
    "<=": operator.le,
    ">": operator.gt,
    "<": operator.lt,
}


def create_annotation(allele_id, num_stars, num_benign, num_uncertain, num_pathogenic, hgmd_tag):
    ann = {}
    ann.setdefault("external", {})
    ann.setdefault("frequencies", {})
    ann.setdefault("prediction", {})
    ann.setdefault("references", [])
    ann.setdefault("transcripts", [])

    clinical_significance_status = {
        1: "criteria provided, conflicting interpretations",
        2: "criteria provided, multiple submitters, no conflicts",
        0: "no assertion criteria provided",
        4: "practice guideline",
        3: "reviewed by expert panel",
    }
    ann["external"]["CLINVAR"] = {
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

    for n in range(num_benign):
        item = dict(item_base)
        item.update({"rcv": "SCVXXXXXXXX", "clinical_significance_descr": "Benign"})
        ann["external"]["CLINVAR"]["items"].append(item)

    for n in range(num_uncertain):
        item = dict(item_base)
        item.update({"rcv": "SCVXXXXXXXX", "clinical_significance_descr": "Uncertain significance"})
        ann["external"]["CLINVAR"]["items"].append(item)

    for n in range(num_pathogenic):
        item = dict(item_base)
        item.update({"rcv": "SCVXXXXXXXX", "clinical_significance_descr": "Pathogenic"})
        ann["external"]["CLINVAR"]["items"].append(item)

    if hgmd_tag:
        ann["external"]["HGMD"] = {"tag": hgmd_tag, "acc_num": "dabla", "disease": "dabla"}

    if not ann["external"]["CLINVAR"]["items"]:
        item = dict(item_base)
        item.update({"rcv": "SCVXXXXXXXX", "clinical_significance_descr": "something"})
        ann["external"]["CLINVAR"]["items"].append(item)

    return annotation.Annotation(allele_id=allele_id, annotations=ann)


@st.composite
def annotations(draw):
    ann = []
    annotation_objs = []
    for i in range(1, 10):
        num_benign = draw(st.integers(min_value=0, max_value=5))
        num_uncertain = draw(st.integers(min_value=0, max_value=5))
        num_pathogenic = draw(st.integers(min_value=0, max_value=5))
        num_stars = draw(st.integers(min_value=0, max_value=4))
        hgmd_tag = draw(st.sampled_from([None, "FP", "DM", "DFP", "R", "DP", "DM?"]))

        ann.append(
            {
                "allele_id": i,
                "num_benign": num_benign,
                "num_uncertain": num_uncertain,
                "num_pathogenic": num_pathogenic,
                "num_stars": num_stars,
                "hgmd_tag": hgmd_tag,
            }
        )
        annotation_objs.append(
            create_annotation(i, num_stars, num_benign, num_uncertain, num_pathogenic, hgmd_tag)
        )

    return ann, annotation_objs


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
    st.one_of(annotations()),
    st.lists(clinvar_strategy(), max_size=3),
    st.one_of(clinvar_stars()),
    st.one_of(st.booleans()),
    st.one_of(hgmd_strategy()),
    st.one_of(st.booleans()),
)
@ht.settings(deadline=500)
def test_externalfilter(
    session,
    annotations,
    clinvar_strategy,
    clinvar_stars,
    clinvar_inverse,
    hgmd_strategy,
    hgmd_inverse,
):
    session.rollback()
    anno_dicts, annotation_objs = annotations

    for obj in annotation_objs:
        existing = (
            session.query(annotation.Annotation)
            .filter(annotation.Annotation.allele_id == obj.allele_id)
            .one()
        )
        existing.date_superceeded = datetime.datetime.now(pytz.utc)
        obj.previous_annotation_id = existing.id

        session.add(obj)
    session.flush()

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

    allele_ids = [1, 2, 3, 4, 5, 6, 7, 8, 9]
    testdata = {"key": allele_ids}

    # Compute clinvar result
    if clinvar_stars or clinvar_strategy:
        clinvar_result = []
        for ann in anno_dicts:
            allele_id = ann["allele_id"]

            if clinvar_stars:
                op, count = clinvar_stars
                if not OPERATORS[op](ann["num_stars"], count):
                    continue

            flag = False
            for c in clinvar_strategy:
                ca, op, cb = c
                ca = ann.get("num_" + str(ca), ca)
                cb = ann.get("num_" + str(cb), cb)
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
        for ann in anno_dicts:
            allele_id = ann["allele_id"]
            if not ann["hgmd_tag"] in hgmd_strategy:
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
