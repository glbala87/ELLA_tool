import base64
import json
import re
import string
from typing import Any, Dict, Mapping, Sequence, Union

import hypothesis as ht
import hypothesis.strategies as st
from conftest import cc
from vardb.deposit.annotationconverters import ConverterArgs
from vardb.deposit.annotationconverters.referenceconverters import (
    _HGMD_SUBSTITUTE,
    ClinVarReferencesConverter,
    HGMDExtraRefsConverter,
    HGMDPrimaryReportConverter,
    RefTag,
)


@st.composite
def hgmd_text(draw) -> str:
    text = draw(st.text(string.ascii_letters + "".join([x[1] for x in _HGMD_SUBSTITUTE])))
    for x in _HGMD_SUBSTITUTE:
        text = re.sub(x[1], x[0].pattern, text)
    return text


@st.composite
def reference(draw) -> Dict[str, Union[str, int]]:
    pmid: int = draw(st.integers(min_value=1, max_value=1e7))
    reftag: str = draw(st.sampled_from(RefTag.tag_strings()))
    comments: str = draw(hgmd_text())

    return {"pmid": pmid, "reftag": reftag, "comments": comments}


@st.composite
def extraref_format(draw) -> Sequence[str]:
    required_fields = ["pmid", "comments", "reftag"]
    N: int = draw(st.integers(min_value=0, max_value=10))
    additional_fields = [f"unused_field{i}" for i in range(N)]
    return draw(st.permutations(required_fields + additional_fields))


@ht.given(st.one_of(extraref_format()), st.lists(reference(), min_size=1, max_size=10))
def test_get_HGMD_extrarefs(extraref_format: str, references: Sequence[Mapping[str, Any]]):
    # Header line as it is parsed dfrom the VCF
    meta = {
        "Description": f"Format: ({'|'.join(extraref_format)}) (from /anno/data/variantDBs/HGMD/hgmd-2018.1_norm.vcf.gz)"
    }
    pmid_idx = extraref_format.index("pmid")
    comment_idx = extraref_format.index("comments")
    reftag_idx = extraref_format.index("reftag")
    data = [[""] * len(extraref_format) for _ in range(len(references))]
    for i, ref in enumerate(references):
        data[i][pmid_idx] = str(ref["pmid"])
        data[i][comment_idx] = ref["comments"]
        data[i][reftag_idx] = ref["reftag"]

    converter = HGMDExtraRefsConverter(meta=meta, config=cc.hgmdextrarefs())
    converter.setup()
    raw = ",".join("|".join(x) for x in data)
    converted = converter(ConverterArgs(raw))
    assert len(converted) == len(references)
    for converted_ref, input_ref in zip(converted, references):
        assert converted_ref["pubmed_id"] == input_ref["pmid"]
        assert converted_ref["source"] == "HGMD"
        comments = input_ref["comments"] or "No comments."
        if input_ref.get("reftag"):
            reftag = RefTag[input_ref["reftag"]]
        else:
            # reftag not in dict or is ""
            reftag = RefTag.NA
        source_info = f"{reftag}. {comments}"
        for pttrn, sub in _HGMD_SUBSTITUTE:
            source_info = re.sub(pttrn, sub, source_info)
        assert converted_ref["source_info"] == source_info


@ht.given(st.one_of(st.integers(min_value=1, max_value=1e7)), st.one_of(hgmd_text()))
def test_HGMD_primaryreport(pmid: int, comments: str):
    converter = HGMDPrimaryReportConverter(config=cc.hgmdprimaryreport())
    expected_source_info = "Primary literature report. No comments."
    for additional_values in [
        {},
        {"HGMD__comments": "None"},
        {"HGMD__comments": None},
        {"HGMD__comments": ""},
    ]:
        converted = converter(ConverterArgs(pmid, additional_values))
        assert len(converted) == 1
        assert converted[0] == {
            "pubmed_id": pmid,
            "source": "HGMD",
            "source_info": expected_source_info,
        }

    additional_values = {"HGMD__comments": comments}
    expected_source_info = f"Primary literature report. {comments if comments else 'No comments.'}"
    for pttrn, sub in _HGMD_SUBSTITUTE:
        expected_source_info = re.sub(pttrn, sub, expected_source_info)

    converted = converter(ConverterArgs(pmid, additional_values))
    assert len(converted) == 1
    assert converted[0] == {
        "pubmed_id": pmid,
        "source": "HGMD",
        "source_info": expected_source_info,
    }


@ht.given(st.lists(st.integers(min_value=1, max_value=1e7), min_size=1, max_size=10))
def test_clinvar_reference(pmids: Sequence[int]):
    converter = ClinVarReferencesConverter(config=cc.clinvarreferences())
    for key in ["pubmeds", "pubmed_ids"]:
        clinvarjson = {key: pmids}
        data = base64.b16encode(json.dumps(clinvarjson).encode())
        converted = converter(ConverterArgs(data))
        assert len(converted) == len(pmids)
        for reference, pmid in zip(converted, pmids):
            assert reference == {"pubmed_id": pmid, "source": "CLINVAR", "source_info": ""}
