from api.allelefilter.qualityfilter import QualityFilter
from vardb.datamodel import sample, allele, genotype

import hypothesis as ht
import hypothesis.strategies as st

allele_start = 1300


def create_allele(data=None):
    global allele_start
    allele_start += 1
    default_allele_data = {
        "chromosome": "1",
        "start_position": allele_start,
        "open_end_position": allele_start + 1,
        "change_from": "A",
        "change_to": "T",
        "change_type": "SNP",
        "vcf_pos": allele_start + 1,
        "vcf_ref": "A",
        "vcf_alt": "T",
    }
    if data:
        for k in data:
            default_allele_data[k] = data[k]
    data = default_allele_data

    return allele.Allele(genome_reference="GRCh37", **data)


def add_data(session, gt_data):
    analysis = sample.Analysis(
        **{"name": "QualityTest", "genepanel_name": "HBOC", "genepanel_version": "v01"}
    )
    session.add(analysis)
    session.flush()
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

    allele_genotype_data = {}
    for data in gt_data:
        al = create_allele()
        session.add(al)
        session.flush()

        gt = genotype.Genotype(
            allele_id=al.id, sample_id=sa.id, variant_quality=data["variant_quality"]
        )
        session.add(gt)
        session.flush()

        gsd = genotype.GenotypeSampleData(
            sample_id=sa.id,
            genotype_id=gt.id,
            allele_ratio=data["genotype_allele_ratio"],
            type="Heterozygous",
            secondallele=False,
            multiallelic=False,
        )

        session.add(gsd)
        session.flush()

        allele_genotype_data[al.id] = data

    return analysis.id, allele_genotype_data


@st.composite
def filter_data(draw):
    return {
        "variant_quality": draw(st.integers(min_value=0, max_value=250)),
        "genotype_allele_ratio": draw(st.floats(min_value=0, max_value=1.0, width=16)),
    }


@st.composite
def filter_config(draw):
    fc = {}
    has_qual = draw(st.booleans())
    if has_qual:
        fc["qual"] = draw(st.integers(min_value=0, max_value=250))
    has_ar = draw(st.booleans())
    if has_ar:
        fc["allele_ratio"] = draw(st.floats(min_value=0, max_value=1.0, width=16))

    ht.assume(has_ar or has_qual)  # Disallow empty filterconfig
    return fc


@ht.example(
    [{"genotype_allele_ratio": 0.24, "variant_quality": 100}],
    {"qual": 100, "allele_ratio": 0.25},
    False,
)  # Should not filter where only one criteria if fulfilled (in this case, allele_ratio)
@ht.example(
    [{"genotype_allele_ratio": 0.26, "variant_quality": 99}],
    {"qual": 100, "allele_ratio": 0.25},
    False,
)  # Should not filter where only one criteria if fulfilled (in this case, variant_quality)
@ht.example(
    [{"genotype_allele_ratio": 0.24, "variant_quality": 99}],
    {"qual": 100, "allele_ratio": 0.25},
    True,
)  # Should filter when both criteria fulfilled
@ht.example(
    [{"genotype_allele_ratio": 0.24, "variant_quality": 99}], {"allele_ratio": 0.25}, True
)  # Should disregard variant quality when not set in filter config
@ht.example(
    [{"genotype_allele_ratio": 0.26, "variant_quality": 99}], {"allele_ratio": 0.25}, False
)  # Should disregard variant quality when not set in filter config
@ht.example(
    [{"genotype_allele_ratio": 0.24, "variant_quality": 99}], {"qual": 100}, True
)  # Should disregard allele ratio when not set in filter config
@ht.example(
    [{"genotype_allele_ratio": 0.24, "variant_quality": 101}], {"qual": 100}, False
)  # Should disregard allele ratio when not set in filter config
@ht.example(
    [{"genotype_allele_ratio": 0.24, "variant_quality": None}], {"qual": 100}, False
)  # Should not filter out alleles with QUAL null
@ht.example(
    [{"genotype_allele_ratio": None, "variant_quality": 99}], {"allele_ratio": 0.25}, False
)  # Should not filter out alleles with AR null
@ht.example(
    [{"genotype_allele_ratio": 0.0, "variant_quality": 99}], {"allele_ratio": 0.25}, False
)  # Should not filter out alleles with AR==0.0
@ht.given(st.lists(filter_data(), min_size=1), st.one_of(filter_config()), st.just(None))
@ht.settings(deadline=500)
def test_classificationfilter(session, genotype_data, fc, manually_curated_result):
    session.rollback()
    # Add generated data to database
    analysis_id, allele_genotype_data = add_data(session, genotype_data)

    # Run filter
    qf = QualityFilter(session, None)
    allele_ids = [int(k) for k in allele_genotype_data.keys()]
    result = qf.filter_alleles({analysis_id: allele_ids}, fc)[analysis_id]

    # Check manually curated result if provided
    if manually_curated_result is not None:
        if manually_curated_result:
            assert set(result) == set(allele_ids)
        else:
            assert set(result) == set()

    expected_result = []
    for allele_id, gt_data in allele_genotype_data.items():
        if "qual" in fc and (
            gt_data["variant_quality"] is None or gt_data["variant_quality"] >= fc["qual"]
        ):
            # Variant quality None or too high
            continue
        if "allele_ratio" in fc and (
            gt_data["genotype_allele_ratio"] is None
            or gt_data["genotype_allele_ratio"] == 0.0
            or gt_data["genotype_allele_ratio"] >= fc["allele_ratio"]
        ):
            # Allele ratio None, 0.0 or too high
            continue

        expected_result.append(allele_id)

    assert set(result) == set(expected_result)
