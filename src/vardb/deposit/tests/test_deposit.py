from collections import defaultdict

import hypothesis as ht
from hypothesis import strategies as st
from sqlalchemy import or_
from conftest import mock_record, MockVcfWriter, ped_info_file
from vardb.deposit.deposit_analysis import (
    DepositAnalysis,
    PrefilterBatchGenerator,
    VALID_PREFILTER_KEYS,
)
from vardb.deposit.analysis_config import AnalysisConfigData
from vardb.datamodel import genotype, sample, allele, assessment
from .vcftestgenerator import vcf_family_strategy


import logging

log = logging.getLogger()
# Supress importer input, comment out when debugging
log.setLevel(logging.WARNING)


ANALYSIS_NUM = 0


@st.composite
def prefilter_batch_strategy(draw, max_size=8):
    """
    Generates batches of testdata for
    testing PrefilterBatchGenerator
    """

    ALLELE_POS = 1

    NEARBY_DISTANCE = 3
    FREQ_THRESHOLD = 0.05
    NUM_THRESHOLD = 5000

    batch_size = draw(st.integers(1, max_size))
    batch = list()
    for idx in range(batch_size):

        pos_increment = draw(st.integers(1, NEARBY_DISTANCE + 10))
        ALLELE_POS += pos_increment

        info = {}
        has_freq = draw(st.booleans())
        if has_freq:
            freq_options = [FREQ_THRESHOLD - 0.0001, FREQ_THRESHOLD, FREQ_THRESHOLD + 0.00001]
            num_options = [NUM_THRESHOLD - 1, NUM_THRESHOLD, NUM_THRESHOLD + 1]
            info["GNOMAD_GENOMES__AN"] = draw(st.sampled_from(freq_options))
            info["GNOMAD_GENOMES__AN"] = draw(st.sampled_from(num_options))

        has_mq = draw(st.booleans())
        if has_mq:
            info["MQ"] = draw(st.integers(min_value=0, max_value=40))

        info["__HAS_CLASSIFICATION"] = draw(st.booleans())
        gt = draw(st.sampled_from(["0/1", "./.", "./1", "1/.", "1", "."]))
        is_multiallelic = gt in ["./1", "1/."] and draw(st.booleans())

        if is_multiallelic:
            info["OLD_MULTIALLELIC"] = "abc"
        batch.append([{"POS": ALLELE_POS, "INFO": info}, ["TEST_SAMPLE"], [{"GT": gt}]])

    return batch


# Nearby
@ht.example(
    [
        [
            {
                "POS": 1,
                "INFO": {
                    "GNOMAD_GENOMES__AF": 0.051,
                    "GNOMAD_GENOMES__AN": 5001,
                    "__HAS_CLASSIFICATION": False,
                },
            },
            ["TEST_SAMPLE"],
            [{"GT": "0/1"}],
        ],
        [
            {
                "POS": 3,
                "INFO": {
                    "GNOMAD_GENOMES__AF": 0.051,
                    "GNOMAD_GENOMES__AN": 5001,
                    "__HAS_CLASSIFICATION": False,
                },
            },
            ["TEST_SAMPLE"],
            [{"GT": "0/1"}],
        ],
    ],
    1,
    [["hi_frequency", "position_not_nearby", "no_classification", "non_multiallelic"]],
    [1, 3],  # POS that should be not prefiltered
)
# Classification
@ht.example(
    [
        [
            {
                "POS": 1,
                "INFO": {
                    "GNOMAD_GENOMES__AF": 0.051,
                    "GNOMAD_GENOMES__AN": 5001,
                    "__HAS_CLASSIFICATION": False,
                },
            },
            ["TEST_SAMPLE"],
            [{"GT": "0/1"}],
        ],
        [
            {
                "POS": 10,
                "INFO": {
                    "GNOMAD_GENOMES__AF": 0.051,
                    "GNOMAD_GENOMES__AN": 5001,
                    "__HAS_CLASSIFICATION": True,
                },
            },
            ["TEST_SAMPLE"],
            [{"GT": "0/1"}],
        ],
    ],
    1,
    [["hi_frequency", "position_not_nearby", "no_classification", "non_multiallelic"]],
    [10],
)
# Multiallelic
@ht.example(
    [
        [
            {
                "POS": 1,
                "INFO": {
                    "GNOMAD_GENOMES__AF": 0.051,
                    "GNOMAD_GENOMES__AN": 5001,
                    "OLD_MULTIALLELIC": "1",
                    "__HAS_CLASSIFICATION": False,
                },
            },
            ["TEST_SAMPLE"],
            [{"GT": "./1"}],
        ],
        [
            {
                "POS": 10,
                "INFO": {
                    "GNOMAD_GENOMES__AF": 0.051,
                    "GNOMAD_GENOMES__AN": 5001,
                    "OLD_MULTIALLELIC": "1",
                    "__HAS_CLASSIFICATION": False,
                },
            },
            ["TEST_SAMPLE"],
            [{"GT": "1/."}],
        ],
    ],
    1,
    [["hi_frequency", "position_not_nearby", "no_classification", "non_multiallelic"]],
    [1, 10],
)
# Frequency
@ht.example(
    [
        [{"POS": 1, "INFO": {"__HAS_CLASSIFICATION": False}}, ["TEST_SAMPLE"], [{"GT": "0/1"}]],
        [
            {
                "POS": 10,
                "INFO": {
                    "GNOMAD_GENOMES__AF": 0.051,
                    "GNOMAD_GENOMES__AN": 5001,
                    "__HAS_CLASSIFICATION": False,
                },
            },
            ["TEST_SAMPLE"],
            [{"GT": "0/1"}],
        ],
        [
            {
                "POS": 100,
                "INFO": {
                    "GNOMAD_GENOMES__AF": 0.049,
                    "GNOMAD_GENOMES__AN": 5001,
                    "__HAS_CLASSIFICATION": False,
                },
            },
            ["TEST_SAMPLE"],
            [{"GT": "0/1"}],
        ],
        [
            {
                "POS": 1000,
                "INFO": {
                    "GNOMAD_GENOMES__AF": 0.051,
                    "GNOMAD_GENOMES__AN": 4999,
                    "__HAS_CLASSIFICATION": False,
                },
            },
            ["TEST_SAMPLE"],
            [{"GT": "0/1"}],
        ],
    ],
    1,
    [["hi_frequency", "position_not_nearby", "no_classification", "non_multiallelic"]],
    [1, 100, 1000],
)
# Nearby, but one is failing MQ
@ht.example(
    [
        [{"POS": 1, "INFO": {"__HAS_CLASSIFICATION": False}}, ["TEST_SAMPLE"], [{"GT": "0/1"}]],
        [
            {"POS": 3, "INFO": {"MQ": 0, "__HAS_CLASSIFICATION": False}},
            ["TEST_SAMPLE"],
            [{"GT": "0/1"}],
        ],
        [{"POS": 5, "INFO": {"__HAS_CLASSIFICATION": False}}, ["TEST_SAMPLE"], [{"GT": "0/1"}]],
    ],
    1,
    [["low_mapping_quality"], ["position_not_nearby"]],
    [1, 5],  # Will include both 1 and 5, even though the nearby variant is not included
)
@ht.given(
    prefilter_batch_strategy(),
    st.integers(1, 5),
    st.lists(
        st.lists(st.sampled_from(elements=list(VALID_PREFILTER_KEYS)), min_size=1, unique=True),
        unique_by=lambda x: tuple(sorted(x)),
        max_size=4,
    ),
    st.just(None),
)
def test_prefilterbatchgenerator(
    session, batch, batch_size, prefilters_to_use, manually_curated_result
):
    # Insert classifications if applicable
    session.execute("DELETE FROM alleleassessment")
    batch_records = []
    for variant_kwargs, samples, fmt in batch:
        r = mock_record(variant_kwargs, fmt=fmt, samples=samples)
        batch_records.append(r)

    for r in batch_records:
        if r.annotation().get("__HAS_CLASSIFICATION", False) is True:
            a = (
                session.query(allele.Allele)
                .filter(
                    allele.Allele.chromosome == r.variant.CHROM,
                    allele.Allele.vcf_pos == r.variant.POS,
                    allele.Allele.vcf_ref == r.variant.REF,
                    allele.Allele.vcf_alt == r.variant.ALT[0],
                )
                .one_or_none()
            )

            if a is None:
                a = allele.Allele(**r.build_allele(ref_genome="foo"))
                session.add(a)
                session.flush()

            aa = assessment.AlleleAssessment(
                user_id=1,
                allele_id=a.id,
                classification="1",
                genepanel_name="HBOC",
                genepanel_version="v01",
            )
            session.add(aa)
            session.flush()

    batch_generator = (r for r in batch_records)
    pbg = PrefilterBatchGenerator(
        session, "TEST_SAMPLE", batch_generator, prefilters=prefilters_to_use, batch_size=batch_size
    )

    total_prefiltered_pos = list()
    total_batch_pos = list()
    for prefiltered_batch, received_batch in pbg:
        total_prefiltered_pos += [r.variant.POS for r in prefiltered_batch]
        total_batch_pos += [r.variant.POS for r in received_batch]

    if manually_curated_result is not None:
        assert manually_curated_result == total_prefiltered_pos
    included = list()
    proband_batch = [
        r for r in batch_records if r.sample_genotype("TEST_SAMPLE") not in [(-1, -1), (-1,)]
    ]

    for idx, r in enumerate(proband_batch):
        if not prefilters_to_use:
            included.append(r.variant.POS)
            continue

        if idx == 0:
            prev_pos = -1000
        else:
            prev_pos = proband_batch[idx - 1].variant.POS

        if idx < len(proband_batch) - 1:
            next_pos = proband_batch[idx + 1].variant.POS
        else:
            next_pos = -1000

        nearby = abs(r.variant.POS - prev_pos) <= 3 or abs(r.variant.POS - next_pos) <= 3

        checks = {
            "non_multiallelic": r.annotation().get("OLD_MULTIALLELIC") is None,
            "hi_frequency": (
                float(r.annotation().get("GNOMAD_GENOMES__AF", 0.0)) > 0.05
                and int(r.annotation().get("GNOMAD_GENOMES__AN", 0)) > 5000
            ),
            "position_not_nearby": not nearby,
            "no_classification": r.annotation().get("__HAS_CLASSIFICATION") is not True,
            "low_mapping_quality": float(r.annotation().get("MQ", float("inf"))) < 20,
        }

        assert set(checks.keys()) == set(VALID_PREFILTER_KEYS)

        for prefilter in prefilters_to_use:
            if all(v for k, v in checks.items() if k in prefilter):
                break
        else:
            included.append(r.variant.POS)

    assert included == total_prefiltered_pos
    assert [r.variant.POS for r in batch_records] == total_batch_pos


@ht.given(vcf_family_strategy(6))
@ht.settings(
    deadline=None, max_examples=300, timeout=ht.unlimited
)  # A bit heavy, so few tests by default
def test_analysis_multiple(session, vcf_data):
    global ANALYSIS_NUM
    ANALYSIS_NUM += 1
    analysis_name = "TEST_ANALYSIS {}".format(ANALYSIS_NUM)

    variants, fmts, sample_names, ped_info = vcf_data

    with MockVcfWriter() as writer, ped_info_file(ped_info or {}) as ped_file:
        writer.set_samples(sample_names)
        for variant, fmt in zip(variants, fmts):
            writer.add_variant(variant, fmt)
        writer.close()

        acd = AnalysisConfigData(None)
        acd.update(
            {
                "name": analysis_name,
                "genepanel_name": "HBOCUTV",
                "genepanel_version": "v01",
                "data": [{"vcf": writer.filename, "ped": ped_file if ped_info else None}],
            }
        )

        da = DepositAnalysis(session)
        da.import_vcf(acd)

    # Preload all data
    analysis = session.query(sample.Analysis).filter(sample.Analysis.name == analysis_name).one()

    samples = session.query(sample.Sample).filter(sample.Sample.analysis_id == analysis.id).all()

    genotypes = (
        session.query(genotype.Genotype)
        .filter(genotype.Genotype.sample_id.in_([s.id for s in samples]))
        .all()
    )

    genotypesampledata = (
        session.query(genotype.GenotypeSampleData)
        .filter(genotype.GenotypeSampleData.genotype_id.in_([g.id for g in genotypes]))
        .all()
    )

    alleles = (
        session.query(allele.Allele)
        .filter(
            or_(
                allele.Allele.id.in_([g.allele_id for g in genotypes]),
                allele.Allele.id.in_([g.secondallele_id for g in genotypes if g.secondallele_id]),
            )
        )
        .all()
    )

    proband_variants = [(i, v) for i, v in enumerate(variants) if "1" in fmts[i][0]["GT"]]
    no_coverage_samples = list()
    for idx, sample_name in enumerate(sample_names):
        if all((fmt[idx]["GT"][::2] in [(".", "."), (".",)] for fmt in fmts)):
            no_coverage_samples.append(sample_name)

    # Start checking data
    # Samples
    proband_sample = None
    for sample_name, ped in ped_info.items():
        sa = next(sa for sa in samples if sa.identifier == sample_name)
        if ped["sex"] is not None:
            assert sa.sex == ("Female" if ped["sex"] == "2" else "Male")
        else:
            assert sa.sex is None
        assert sa.affected is (ped["affected"] == "2")
        is_proband = ped["proband"] == "1"
        assert sa.proband is is_proband
        if is_proband:
            assert proband_sample is None
            proband_sample = sa
        assert sa.family_id == ped.get("fam")

        father_name = ped["father"] if "father" in ped and ped["father"] != "0" else None
        mother_name = ped["mother"] if "mother" in ped and ped["mother"] != "0" else None
        if father_name:
            fsa = next(sa for sa in samples if sa.identifier == father_name)
            assert sa.father_id == fsa.id
        if mother_name:
            msa = next(sa for sa in samples if sa.identifier == mother_name)
            assert sa.mother_id == msa.id

        # Samples are ordered, so we know proband is already processed..
        if not is_proband and father_name and mother_name:
            assert sa.sibling_id == proband_sample.id

    # Variants
    if not proband_variants:
        assert not alleles
        assert not genotypes
        assert not genotypesampledata
    else:
        assert len(proband_variants) in [1, 2]
        fixtures = {"allele": {}, "secondallele": {}}
        for idx, variant in proband_variants:
            # Get the correct format for this variant
            sample_data = {k: v for k, v in zip(sample_names, fmts[idx])}
            al = next(
                a
                for a in alleles
                if a.vcf_pos == variant["POS"]
                and a.vcf_ref == variant["REF"]
                and a.vcf_alt == variant["ALT"]
                and a.chromosome == variant["CHROM"]
            )
            key = "allele"
            if tuple(sample_data["PROBAND"]["GT"][::2]) == (".", "1"):
                key = "secondallele"

            fixtures[key]["sample_data"] = sample_data
            fixtures[key]["variant"] = variant
            fixtures[key]["allele"] = al
            for sample_name in sample_data:
                sa = next(sa for sa in samples if sa.identifier == sample_name)
                gsds = [
                    gsd
                    for gsd in genotypesampledata
                    if gsd.sample_id == sa.id
                    and gsd.secondallele is (True if key == "secondallele" else False)
                ]
                assert len(gsds) == 1
                gsd = gsds[0]
                if "genotypesampledata" not in fixtures[key]:
                    fixtures[key]["genotypesampledata"] = dict()
                fixtures[key]["genotypesampledata"][sample_name] = gsd

        gt = next(
            g
            for g in genotypes
            if g.allele_id == fixtures["allele"]["allele"].id
            and g.secondallele_id
            == (fixtures["secondallele"]["allele"].id if fixtures["secondallele"] else None)
        )

        assert gt.variant_quality == 5000
        assert gt.filter_status == "PASS"

        # Allele depth
        sample_allele_depth = defaultdict(dict)
        for i, variant in enumerate(variants):
            for sample_name, sample_data in zip(sample_names, fmts[i]):
                sample_allele_depth[sample_name].update(
                    {
                        k: v
                        for k, v in zip(
                            ["REF ({})".format(variant["REF"]), variant["ALT"]],
                            [int(a) for a in sample_data["AD"].split(",")],
                        )
                    }
                )
        gsd_type = ""
        # Check that genotypesampledata is set correctly
        for key in ["allele", "secondallele"]:
            if key == "secondallele" and not fixtures[key]:
                continue
            for sample_name, data in fixtures[key]["sample_data"].items():
                gsd = fixtures[key]["genotypesampledata"][sample_name]
                if tuple(data["GT"][::2]) in [("1", "1"), ("1",)]:
                    gsd_type = "Homozygous"
                elif tuple(data["GT"][::2]) in [("0", "1"), ("1", "0"), ("1", "."), (".", "1")]:
                    gsd_type = "Heterozygous"
                elif tuple(data["GT"][::2]) in [("0", "0"), ("0", "."), (".", "0"), ("0",)]:
                    gsd_type = "Reference"
                elif tuple(data["GT"][::2]) in [(".", "."), (".",)]:
                    # Proband cannot be reference for it's own variants
                    assert sample_name != "PROBAND"
                    if sample_name in no_coverage_samples:
                        gsd_type = "No coverage"
                    else:
                        # 'Reference' doesn't mean vcf ref,
                        # but with regards to proband's variant
                        gsd_type = "Reference"
                gsd_multiallelic = data["GT"] in [
                    "./1",
                    "1/.",
                    "0/.",
                    "./0",
                    ".|1",
                    "1|.",
                    "0|.",
                    ".|0",
                ]
                assert gsd.type == gsd_type
                assert gsd.multiallelic == gsd_multiallelic
                assert gsd.sequencing_depth == data["DP"]
                if not gsd_multiallelic:
                    assert gsd.genotype_likelihood == [int(p) for p in data["PL"].split(",")]
                else:
                    assert gsd.genotype_likelihood is None
                assert gsd.allele_depth == sample_allele_depth[sample_name]
