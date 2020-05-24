import re
from datalayer.allelefilter.qualityfilter import QualityFilter
from vardb.datamodel import sample, genotype
from conftest import create_allele

import hypothesis as ht
import hypothesis.strategies as st


def add_data(session, gt_data):
    analysis = sample.Analysis(
        **{"name": "QualityTest", "genepanel_name": "HBOC", "genepanel_version": "v01"}
    )
    session.add(analysis)
    session.flush()
    allele_genotype_data = {}

    sample_ids = []

    def get_sample_id(idx):
        while idx >= len(sample_ids):
            sa = sample.Sample(
                **{
                    "identifier": "QualityTestSample",
                    "proband": True,
                    "sample_type": "HTS",
                    "affected": True,
                    "analysis_id": analysis.id,
                }
            )
            session.add(sa)
            session.flush()
            sample_ids.append(sa.id)

        return sample_ids[idx]

    for allele_gts in gt_data:
        al = create_allele()
        session.add(al)
        session.flush()
        allele_genotype_data[al.id] = []

        for i, data in enumerate(allele_gts):
            if data is None:
                # No genotype for this sample
                continue
            sample_id = get_sample_id(i)
            secondallele = bool(
                data.get("variant_quality") is not None and data["variant_quality"] % 7 == 0
            )  # Run some variants with secondallele = True

            gt = genotype.Genotype(
                allele_id=al.id,
                secondallele_id=al.id if secondallele else None,  # Mock the secondallele
                sample_id=sample_id,
                variant_quality=data.get("variant_quality"),
                filter_status=data.get("filter_status"),
            )
            session.add(gt)
            session.flush()

            gsd = genotype.GenotypeSampleData(
                sample_id=sample_id,
                genotype_id=gt.id,
                allele_ratio=data.get("genotype_allele_ratio"),
                type="Heterozygous",
                secondallele=secondallele,
                multiallelic=False,
            )

            session.add(gsd)
            session.flush()

            allele_genotype_data[al.id].append(data)

    return analysis.id, allele_genotype_data


@st.composite
def filter_data(draw):
    N = draw(st.integers(min_value=1, max_value=3))  # Max 3 samples
    gt_data = []
    for i in range(N):
        has_genotype = draw(st.booleans())
        if has_genotype:
            gt_data.append(
                {
                    "filter_status": draw(
                        st.sampled_from([None, "PASS", ".", "VQSRTrancheSNP99.00to99.90"])
                    ),
                    "variant_quality": draw(st.integers(min_value=0, max_value=250)),
                    "genotype_allele_ratio": draw(st.floats(min_value=0, max_value=1.0, width=16)),
                }
            )
        else:
            gt_data = [None] + gt_data
    ht.assume(any(x is not None for x in gt_data))
    return gt_data


@st.composite
def filter_config(draw):
    fc = {}
    has_qual = draw(st.booleans())
    if has_qual:
        fc["qual"] = draw(st.integers(min_value=0, max_value=250))
    has_ar = draw(st.booleans())
    if has_ar:
        fc["allele_ratio"] = draw(st.floats(min_value=0, max_value=1.0, width=16))
    has_filter = draw(st.booleans())
    if has_filter:
        fc["filter_status"] = {
            "pattern": draw(st.sampled_from(["PASS", ".*VQSRTrancheSNP.*"])),
            "inverse": draw(st.booleans()),
            "filter_empty": draw(st.booleans()),
        }

    ht.assume(has_ar or has_qual or has_filter)  # Disallow empty filterconfig
    return fc


@ht.example(
    [[{"genotype_allele_ratio": 0.24, "variant_quality": 100}]],
    {"qual": 100, "allele_ratio": 0.25},
    [],
)  # Should not filter where only one criteria if fulfilled (in this case, allele_ratio)
@ht.example(
    [[{"genotype_allele_ratio": 0.26, "variant_quality": 99}]],
    {"qual": 100, "allele_ratio": 0.25},
    [],
)  # Should not filter where only one criteria if fulfilled (in this case, variant_quality)
@ht.example(
    [[{"genotype_allele_ratio": 0.24, "variant_quality": 99}]],
    {"qual": 100, "allele_ratio": 0.25},
    [0],
)  # Should filter when both criteria fulfilled
@ht.example(
    [[{"genotype_allele_ratio": 0.24, "variant_quality": 99}]], {"allele_ratio": 0.25}, [0]
)  # Should disregard variant quality when not set in filter config
@ht.example(
    [[{"genotype_allele_ratio": 0.26, "variant_quality": 99}]], {"allele_ratio": 0.25}, []
)  # Should disregard variant quality when not set in filter config
@ht.example(
    [[{"genotype_allele_ratio": 0.24, "variant_quality": 99}]], {"qual": 100}, [0]
)  # Should disregard allele ratio when not set in filter config
@ht.example(
    [[{"genotype_allele_ratio": 0.24, "variant_quality": 101}]], {"qual": 100}, []
)  # Should disregard allele ratio when not set in filter config
@ht.example(
    [[{"genotype_allele_ratio": 0.24, "filter_status": "FAIL", "variant_quality": 101}]],
    {"qual": 100},
    [],
)  # Should disregard filter status when not set in filter config
@ht.example(
    [[{"genotype_allele_ratio": 0.24, "variant_quality": None}]], {"qual": 100}, []
)  # Should not filter out alleles with QUAL null
@ht.example(
    [[{"genotype_allele_ratio": None, "variant_quality": 99}]], {"allele_ratio": 0.25}, []
)  # Should not filter out alleles with AR null
@ht.example(
    [[{"genotype_allele_ratio": 0.0, "variant_quality": 99}]], {"allele_ratio": 0.25}, []
)  # Should not filter out alleles with AR==0.0
@ht.example(
    [[{"filter_status": "."}], [{"filter_status": None}]],
    {"filter_status": {"pattern": "\\.", "filter_empty": False}},
    [],
)  # Should not filter out alleles with filter_status None or '.', unless specified
@ht.example(
    [[{"filter_status": "."}], [{"filter_status": None}]],
    {"filter_status": {"pattern": "PASS", "filter_empty": True}},
    [0, 1],
)  # Should filter out alleles with filter_status None or '.' when specified
@ht.example(
    [[{"filter_status": "."}], [{"filter_status": None}]],
    {"filter_status": {"pattern": "PASS", "filter_empty": True, "inverse": True}},
    [],
)  # Should not filter out alleles with filter_status None or '.' when inverse
@ht.example(
    [[{"filter_status": "FAIL"}]], {"filter_status": {"pattern": "PASS", "inverse": True}}, [0]
)  # Should filter out alleles with inverse = True
@ht.example(
    [
        [
            # Sample 1
            {"genotype_allele_ratio": 0.24, "variant_quality": 99},
            # Sample 2, same allele
            {"genotype_allele_ratio": 0.26, "variant_quality": 99},
        ]
    ],
    {"allele_ratio": 0.25},
    [],
)  # Should not filter when not all samples fulfill the criteria for the genotype
@ht.example(
    [
        [
            {"genotype_allele_ratio": 0.24, "variant_quality": 101},
            {"genotype_allele_ratio": 0.26, "variant_quality": 99},
        ]
    ],
    {"qual": 100},
    [],
)  # Should not filter when not all samples fulfill the criteria for the genotype
@ht.example(
    [[{"filter_status": "VQSRTrancheSNP99.00to99.90"}, {"filter_status": "PASS"}]],
    {"filter_status": {"pattern": ".*VQSR.*"}},
    [],
)  # Should not filter when not all samples fulfill the criteria for the genotype
@ht.example(
    [
        [
            {"genotype_allele_ratio": 0.24, "variant_quality": 99},
            {"genotype_allele_ratio": 0.24, "variant_quality": 99},
        ]
    ],
    {"allele_ratio": 0.25},
    [0],
)  # Should filter when all samples fulfill the criteria for the genotype
@ht.example(
    [[{"filter_status": "VQSRTrancheSNP99.00to99.90"}]],
    {"filter_status": {"pattern": ".*VQSRTranche.*"}},
    [0],
)  # Should filter when all samples fulfill the criteria for the genotype
@ht.example(
    [
        [None, {"genotype_allele_ratio": 0.24, "variant_quality": 99}],
        [{"genotype_allele_ratio": 0.24, "variant_quality": 99}],
    ],
    {"allele_ratio": 0.25},
    [0, 1],
)  # Should filter if one sample does not have the genotype
@ht.example(
    [
        [None, {"genotype_allele_ratio": 0.26, "variant_quality": 99}],
        [{"genotype_allele_ratio": 0.24, "variant_quality": 99}],
    ],
    {"allele_ratio": 0.25},
    [1],
)  # Should filter if one sample does not have the genotype
@ht.example(
    [
        [None, {"genotype_allele_ratio": 0.24, "variant_quality": 99}],
        [{"genotype_allele_ratio": 0.24, "variant_quality": 101}],
    ],
    {"qual": 100},
    [0],
)  # Should filter if one sample does not have the genotype
@ht.example(
    [
        [None, {"genotype_allele_ratio": 0.26, "variant_quality": 99}],
        [{"genotype_allele_ratio": 0.26, "variant_quality": 99}],
    ],
    {"allele_ratio": 0.25},
    [],
)  # Should filter if one sample does not have the genotype
@ht.example(
    [
        [None, {"genotype_allele_ratio": 0.26, "variant_quality": 99, "filter_status": "PASS"}],
        [{"genotype_allele_ratio": 0.26, "variant_quality": 99, "filter_status": "PASS"}],
    ],
    {"filter_status": {"pattern": "PASS"}},
    [0, 1],
)  # Should filter if one sample does not have the genotype
@ht.given(st.lists(filter_data(), min_size=1), st.one_of(filter_config()), st.just(None))
@ht.settings(deadline=500)
def test_qualityfilter(session, genotype_data, fc, manually_curated_result):
    """genotype_data is of the form:
    [
        [sample1 genotype, sample2 genotype, ...], # Allele 1
        [sample1 genotype, sample2 genotype, ...], # Allele 2
    ]
    """
    session.rollback()

    # Add generated data to database
    analysis_id, allele_genotype_data = add_data(session, genotype_data)

    # Run filter
    qf = QualityFilter(session, None)
    allele_ids = [int(k) for k in allele_genotype_data.keys()]
    result = qf.filter_alleles({analysis_id: allele_ids}, fc)[analysis_id]

    # Check manually curated result if provided
    if manually_curated_result is not None:
        assert set(result) == set(allele_ids[k] for k in manually_curated_result)

    expected_result = []
    for allele_id, sample_gt_data in allele_genotype_data.items():
        if "qual" in fc and any(
            gt_data["variant_quality"] is None or gt_data["variant_quality"] >= fc["qual"]
            for gt_data in sample_gt_data
            if gt_data is not None
        ):
            # Variant quality None or above threshold
            continue
        if "allele_ratio" in fc and any(
            gt_data["genotype_allele_ratio"] is None
            or gt_data["genotype_allele_ratio"] == 0.0
            or gt_data["genotype_allele_ratio"] >= fc["allele_ratio"]
            for gt_data in sample_gt_data
            if gt_data is not None
        ):
            # Allele ratio None, 0.0 or above threshold
            continue

        if "filter_status" in fc:

            def apply_filter(text):
                def apply_inverse(result):
                    return not result if fc["filter_status"].get("inverse") else result

                if text is None or text == ".":
                    return apply_inverse(fc["filter_status"].get("filter_empty"))

                pattern = re.compile(fc["filter_status"]["pattern"])
                match = bool(re.match(pattern, text))
                return apply_inverse(match)

            # ALL samples must be filtered for allele to be filtered
            if any(
                not apply_filter(gt_data["filter_status"])
                for gt_data in sample_gt_data
                if gt_data is not None
            ):
                continue

        expected_result.append(allele_id)

    assert set(result) == set(expected_result)
