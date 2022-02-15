import hypothesis as ht
from hypothesis import strategies as st
import tempfile
import os
import shutil
import string
from contextlib import contextmanager
from pathlib import Path
import json

from ..analysis_config import AnalysisConfigData

WARNING_TEXT = "Some warnings"
REPORT_TEXT = "Some report text"


@contextmanager
def temporary_directory(dirname="analysisconfigdata"):
    tmp_dir = Path(tempfile.gettempdir())
    full_path = tmp_dir / dirname
    os.mkdir(full_path)
    try:
        yield full_path
    finally:
        shutil.rmtree(full_path)


def create_file(folder, name, contents=None):
    full_path = folder / name
    with full_path.open("w") as f:
        if contents:
            f.write(contents)
    return full_path


@ht.given(
    st.text(string.ascii_letters, min_size=1),
    st.text(string.ascii_letters, min_size=1),
    st.text(string.ascii_letters, min_size=1),
    st.text(string.ascii_letters, min_size=1),
    st.booleans(),
    st.booleans(),
    st.booleans(),
    st.one_of(st.just(None), st.integers(min_value=1, max_value=3)),
    st.one_of(st.just(None), st.dates()),
    st.one_of(st.just(".vcf"), st.just(".vcf.gz")),
)
def test_legacy_analysis_file(
    filename_stem,
    analysis_name,
    genepanel_name,
    genepanel_version,
    has_ped,
    has_warnings,
    has_report,
    priority,
    date_requested,
    vcf_suffix,
):

    legacy_analysis_file = {
        "name": analysis_name,
        "params": {"genepanel": genepanel_name + "_" + genepanel_version},
    }
    if priority is not None:
        legacy_analysis_file["priority"] = priority

    if date_requested is not None:
        legacy_analysis_file["date_requested"] = str(date_requested)
    with temporary_directory() as d:
        analysis_file = create_file(
            d, filename_stem + ".analysis", json.dumps(legacy_analysis_file)
        )
        create_file(d, filename_stem + vcf_suffix)
        if has_ped:
            create_file(d, filename_stem + ".ped")

        if has_warnings:
            create_file(d, "warnings.txt", WARNING_TEXT)

        if has_report:
            create_file(d, "report.txt", REPORT_TEXT)

        acd = AnalysisConfigData(analysis_file)

    expected = {
        "name": analysis_name,
        "genepanel_name": genepanel_name,
        "genepanel_version": genepanel_version,
        "report": REPORT_TEXT if has_report else None,
        "warnings": WARNING_TEXT if has_warnings else None,
        "priority": 1 if priority is None else priority,
        "data": [
            {
                "vcf": str(d / (filename_stem + vcf_suffix)),
                "ped": str(d / (filename_stem + ".ped")) if has_ped else None,
                "technology": "HTS",
            }
        ],
    }
    if date_requested is not None:
        expected["date_requested"] = str(date_requested)

    assert acd == expected


@ht.given(
    st.text(string.ascii_letters, min_size=1),
    st.text(string.ascii_letters, min_size=1),
    st.text(string.ascii_letters, min_size=1),
    st.text(string.ascii_letters, min_size=1),
    st.lists(
        st.tuples(
            st.booleans(),
            st.sampled_from([None, "Technology1", "Technology2"]),
            st.sampled_from([None, "Caller1", "Caller2"]),
        ),
        min_size=1,
    ),
    st.one_of(st.just(".vcf"), st.just(".vcf.gz")),
)
def test_analysis_file(
    filename_stem,
    analysis_name,
    genepanel_name,
    genepanel_version,
    data,
    vcf_suffix,
):
    analysis_file_contents = {
        "name": analysis_name,
        "genepanel_name": genepanel_name,
        "genepanel_version": genepanel_version,
        "data": [],
    }
    with temporary_directory() as d:
        for i, (has_ped, technology, caller) in enumerate(data):
            entry = {"vcf": f"vcf_file{i}" + vcf_suffix}
            create_file(d, f"vcf_file{i}" + vcf_suffix)
            if has_ped:
                create_file(d, f"ped_file{i}.ped")
                entry["ped"] = f"ped_file{i}.ped"

            if technology is not None:
                entry["technology"] = technology

            if caller is not None:
                entry["callerName"] = caller

            analysis_file_contents["data"].append(entry)

        analysis_file = create_file(
            d, filename_stem + ".analysis", json.dumps(analysis_file_contents, indent=4)
        )

        acd_file = AnalysisConfigData(analysis_file)
        acd_folder = AnalysisConfigData(d)

    assert acd_file == acd_folder

    expected = dict(analysis_file_contents)
    expected.setdefault("priority", 1)
    expected.setdefault("warnings", None)
    expected.setdefault("report", None)
    for entry in expected["data"]:
        entry["vcf"] = str(d / entry["vcf"])
        if "ped" in entry:
            entry["ped"] = str(d / entry["ped"])
        else:
            entry["ped"] = None

        entry.setdefault("technology", "HTS")

    assert expected == acd_file


@ht.given(
    st.text(string.ascii_letters, min_size=1),
    st.text(string.ascii_letters, min_size=1),
    st.text(string.ascii_letters, min_size=1),
    st.sampled_from([".", "-"]),
    st.sampled_from(["_", "-"]),
)
def test_from_vcf(sample_name, genepanel_name, genepanel_version, sep1, sep2):
    analysis_name = f"{sample_name}{sep1}{genepanel_name}{sep2}{genepanel_version}"

    with temporary_directory() as d:
        f = create_file(d, f"{analysis_name}.vcf.gz")
        create_file(d, "warnings.txt", "Some warnings that are ignored")
        create_file(d, "report.txt", "Some report that's ignored")
        acd = AnalysisConfigData(f)

        expected = {
            "name": analysis_name,
            "genepanel_name": genepanel_name,
            "genepanel_version": genepanel_version,
            "warnings": None,
            "report": None,
            "priority": 1,
            "data": [{"vcf": str(f), "ped": None, "technology": "HTS"}],
        }
        assert acd == expected


@ht.given(
    st.text(string.ascii_letters, min_size=1),
    st.text(string.ascii_letters, min_size=1),
    st.text(string.ascii_letters, min_size=1),
    st.sampled_from([".", "-"]),
    st.sampled_from(["_", "-"]),
    st.booleans(),
    st.booleans(),
    st.lists(st.booleans(), min_size=1),
    st.one_of(st.just(".vcf"), st.just(".vcf.gz")),
)
def test_from_folder(
    sample_name,
    genepanel_name,
    genepanel_version,
    sep1,
    sep2,
    has_warnings,
    has_report,
    vcf_with_ped_file,
    vcf_suffix,
):
    analysis_name = f"{sample_name}{sep1}{genepanel_name}{sep2}{genepanel_version}"

    with temporary_directory(analysis_name) as d:
        expected_data = []
        for i, with_ped in enumerate(vcf_with_ped_file):
            vcf = str(create_file(d, f"file{i}" + vcf_suffix))
            if with_ped:
                ped = str(create_file(d, f"file{i}.ped"))
            else:
                ped = None
            expected_data.append({"vcf": vcf, "ped": ped, "technology": "HTS"})

        expected_data = sorted(expected_data, key=lambda x: x["vcf"])

        if has_warnings:
            create_file(d, "warnings.txt", WARNING_TEXT)

        if has_report:
            create_file(d, "report.txt", REPORT_TEXT)

        acd = AnalysisConfigData(d)

    expected = {
        "name": analysis_name,
        "genepanel_name": genepanel_name,
        "genepanel_version": genepanel_version,
        "warnings": WARNING_TEXT if has_warnings else None,
        "report": REPORT_TEXT if has_report else None,
        "priority": 1,
        "data": expected_data,
    }

    assert expected == acd
