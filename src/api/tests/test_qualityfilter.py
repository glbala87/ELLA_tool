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

        gt = genotype.Genotype(allele_id=al.id, sample_id=sa.id, variant_quality=data["qual"])
        session.add(gt)
        session.flush()

        gsd = genotype.GenotypeSampleData(
            sample_id=sa.id,
            genotype_id=gt.id,
            allele_ratio=data["ar"],
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
        "qual": draw(st.integers(min_value=0, max_value=250)),
        "ar": draw(st.floats(min_value=0, max_value=1.0, width=16)),
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


@ht.example([{"ar": 0.24, "qual": 101}], {"qual": 100, "allele_ratio": 0.25}, False)
@ht.example([{"ar": 0.26, "qual": 99}], {"qual": 100, "allele_ratio": 0.25}, False)
@ht.example([{"ar": 0.24, "qual": 99}], {"qual": 100, "allele_ratio": 0.25}, True)
@ht.example([{"ar": 0.24, "qual": 99}], {"allele_ratio": 0.25}, True)
@ht.example([{"ar": 0.26, "qual": 99}], {"allele_ratio": 0.25}, False)
@ht.example([{"ar": 0.24, "qual": 99}], {"qual": 100}, True)
@ht.example([{"ar": 0.24, "qual": 101}], {"qual": 100}, False)
@ht.example(
    [{"ar": 0.24, "qual": None}], {"qual": 100}, False
)  # Should not filter out alleles with QUAL null
@ht.example(
    [{"ar": None, "qual": 99}], {"allele_ratio": 0.25}, False
)  # Should not filter out alleles with AR null
@ht.example(
    [{"ar": 0.0, "qual": 99}], {"allele_ratio": 0.25}, False
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
    qual_threshold = fc.get("qual")
    ar_threshold = fc.get("allele_ratio")
    for allele_id, gt_data in allele_genotype_data.items():
        if (
            qual_threshold is None
            or (gt_data["qual"] is not None and gt_data["qual"] < qual_threshold)
        ) and (
            ar_threshold is None
            or (gt_data["ar"] is not None and 0.0 < gt_data["ar"] < ar_threshold)
        ):
            expected_result.append(allele_id)

    assert set(result) == set(expected_result)
