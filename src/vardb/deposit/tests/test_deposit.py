import os
import tempfile
from collections import defaultdict
from contextlib import contextmanager

import hypothesis as ht
from hypothesis import strategies as st
from sqlalchemy import or_
from vardb.deposit.deposit_alleles import DepositAlleles
from vardb.deposit.deposit_analysis import (
    DepositAnalysis,
    PrefilterBatchGenerator,
    MultiAllelicBlockIterator,
)
from vardb.datamodel.analysis_config import AnalysisConfigData
from vardb.datamodel import genotype, sample, allele, assessment
from .vcftestgenerator import vcf_family_strategy

import logging

log = logging.getLogger()
# Supress importer input, comment out when debugging
log.setLevel(logging.WARNING)


@contextmanager
def tempinput(data: str):
    temp = tempfile.NamedTemporaryFile(delete=False)
    temp.write(data.encode())
    temp.close()
    try:
        yield temp.name
    finally:
        os.unlink(temp.name)


ANALYSIS_NUM = 0


@st.composite
def prefilter_batch_strategy(draw, max_size=5):
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

        pos_increment = draw(st.integers(NEARBY_DISTANCE - 1, NEARBY_DISTANCE + 10))
        ALLELE_POS += pos_increment
        record = {
            "CHROM": "1",
            "POS": ALLELE_POS,
            "REF": "A",
            "ALT": ["T"],
            "SAMPLES": {
                "TEST_SAMPLE": {
                    "GT": draw(
                        st.sampled_from(
                            ["0/1", "./.", "./1", "1/.", "0|1", "1|0", ".|.", ".|1", "1|."]
                        )
                    )
                }
            },
            "INFO": {"ALL": {}},
        }
        has_freq = draw(st.booleans())
        if has_freq:
            freq_options = [FREQ_THRESHOLD - 0.0001, FREQ_THRESHOLD, FREQ_THRESHOLD + 0.00001]
            num_options = [NUM_THRESHOLD - 1, NUM_THRESHOLD, NUM_THRESHOLD + 1]
            record["INFO"]["ALL"]["GNOMAD_GENOMES"] = {
                "AF": [draw(st.sampled_from(freq_options))],
                "AN": draw(st.sampled_from(num_options)),
            }

        # Whether to simulate classification for this record
        record["__HAS_CLASSIFICATION"] = draw(st.booleans())

        batch.append(record)
    return batch


# Nearby
@ht.example(
    [
        {
            "CHROM": "1",
            "POS": 1,
            "REF": "A",
            "ALT": ["T"],
            "SAMPLES": {"TEST_SAMPLE": {"GT": "0/1"}},
            "INFO": {"ALL": {"GNOMAD_GENOMES": {"AF": [0.051], "AN": 5001}}},
            "__HAS_CLASSIFICATION": False,
        },
        {
            "CHROM": "1",
            "POS": 3,
            "REF": "A",
            "ALT": ["T"],
            "SAMPLES": {"TEST_SAMPLE": {"GT": "0/1"}},
            "INFO": {"ALL": {"GNOMAD_GENOMES": {"AF": [0.051], "AN": 5001}}},
            "__HAS_CLASSIFICATION": False,
        },
    ],
    1,
    [1, 3],  # POS that should be not prefiltered
)
# Classification
@ht.example(
    [
        {
            "CHROM": "1",
            "POS": 1,
            "REF": "A",
            "ALT": ["T"],
            "SAMPLES": {"TEST_SAMPLE": {"GT": "0/1"}},
            "INFO": {"ALL": {"GNOMAD_GENOMES": {"AF": [0.051], "AN": 5001}}},
            "__HAS_CLASSIFICATION": False,
        },
        {
            "CHROM": "1",
            "POS": 10,
            "REF": "A",
            "ALT": ["T"],
            "SAMPLES": {"TEST_SAMPLE": {"GT": "0/1"}},
            "INFO": {"ALL": {"GNOMAD_GENOMES": {"AF": [0.051], "AN": 5001}}},
            "__HAS_CLASSIFICATION": True,
        },
    ],
    1,
    [1, 10],
)
# Multiallelic
@ht.example(
    [
        {
            "CHROM": "1",
            "POS": 1,
            "REF": "A",
            "ALT": ["T"],
            "SAMPLES": {"TEST_SAMPLE": {"GT": "./1"}},
            "INFO": {"ALL": {"GNOMAD_GENOMES": {"AF": [0.051], "AN": 5001}}},
            "__HAS_CLASSIFICATION": False,
        },
        {
            "CHROM": "1",
            "POS": 10,
            "REF": "A",
            "ALT": ["T"],
            "SAMPLES": {"TEST_SAMPLE": {"GT": "1/."}},
            "INFO": {"ALL": {"GNOMAD_GENOMES": {"AF": [0.051], "AN": 5001}}},
            "__HAS_CLASSIFICATION": False,
        },
    ],
    1,
    [1, 10],
)
# Multiallelic
@ht.example(
    [
        {
            "CHROM": "1",
            "POS": 1,
            "REF": "A",
            "ALT": ["T"],
            "SAMPLES": {"TEST_SAMPLE": {"GT": ".|1"}},
            "INFO": {"ALL": {"GNOMAD_GENOMES": {"AF": [0.051], "AN": 5001}}},
            "__HAS_CLASSIFICATION": False,
        },
        {
            "CHROM": "1",
            "POS": 10,
            "REF": "A",
            "ALT": ["T"],
            "SAMPLES": {"TEST_SAMPLE": {"GT": "1|."}},
            "INFO": {"ALL": {"GNOMAD_GENOMES": {"AF": [0.051], "AN": 5001}}},
            "__HAS_CLASSIFICATION": False,
        },
    ],
    1,
    [1, 10],
)
# Frequency
@ht.example(
    [
        {
            "CHROM": "1",
            "POS": 1,
            "REF": "A",
            "ALT": ["T"],
            "SAMPLES": {"TEST_SAMPLE": {"GT": "0/1"}},
            "INFO": {"ALL": {}},
            "__HAS_CLASSIFICATION": False,
        },
        {
            "CHROM": "1",
            "POS": 10,
            "REF": "A",
            "ALT": ["T"],
            "SAMPLES": {"TEST_SAMPLE": {"GT": "0/1"}},
            "INFO": {"ALL": {"GNOMAD_GENOMES": {"AF": [0.051], "AN": 5001}}},
            "__HAS_CLASSIFICATION": False,
        },
        {
            "CHROM": "1",
            "POS": 100,
            "REF": "A",
            "ALT": ["T"],
            "SAMPLES": {"TEST_SAMPLE": {"GT": "0/1"}},
            "INFO": {"ALL": {"GNOMAD_GENOMES": {"AF": [0.049], "AN": 5001}}},
            "__HAS_CLASSIFICATION": False,
        },
        {
            "CHROM": "1",
            "POS": 1000,
            "REF": "A",
            "ALT": ["T"],
            "SAMPLES": {"TEST_SAMPLE": {"GT": "0/1"}},
            "INFO": {"ALL": {"GNOMAD_GENOMES": {"AF": [0.051], "AN": 4999}}},
            "__HAS_CLASSIFICATION": False,
        },
    ],
    1,
    [1, 100, 1000],
)
@ht.given(prefilter_batch_strategy(), st.integers(1, 5), st.just(None))
def test_prefilterbatchgenerator(session, batch, batch_size, manually_curated_result):

    # Insert classifications if applicable
    session.execute("DELETE FROM alleleassessment")

    for r in batch:
        if r["__HAS_CLASSIFICATION"]:
            a = (
                session.query(allele.Allele)
                .filter(
                    allele.Allele.chromosome == r["CHROM"],
                    allele.Allele.vcf_pos == r["POS"],
                    allele.Allele.vcf_ref == r["REF"],
                    allele.Allele.vcf_alt == r["ALT"][0],
                )
                .one_or_none()
            )

            if a is None:
                a = allele.Allele(
                    genome_reference="foo",
                    chromosome=r["CHROM"],
                    start_position=r["POS"],
                    open_end_position=r["POS"] + 1,
                    change_from=r["REF"],
                    change_to=r["ALT"][0],
                    change_type="SNP",
                    vcf_pos=r["POS"],
                    vcf_ref=r["REF"],
                    vcf_alt=r["ALT"][0],
                )
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
            session.commit()

    batch_generator = (r for r in batch)
    pbg = PrefilterBatchGenerator(
        session, "TEST_SAMPLE", batch_generator, prefilter=True, batch_size=batch_size
    )

    total_prefiltered = list()
    total_batch = list()
    for prefiltered_batch, received_batch in pbg:
        total_prefiltered += prefiltered_batch
        total_batch += received_batch

    if manually_curated_result is not None:
        total_prefiltered_pos = [r["POS"] for r in total_prefiltered]
        assert manually_curated_result == total_prefiltered_pos

    included = list()
    proband_batch = [r for r in batch if r["SAMPLES"]["TEST_SAMPLE"]["GT"] not in ["./.", ".|."]]
    for idx, r in enumerate(proband_batch):

        if idx == 0:
            # Implementation always includes first record due to no previous
            prev_pos = r["POS"]
        else:
            prev_pos = proband_batch[idx - 1]["POS"]

        if idx < len(proband_batch) - 1:
            next_pos = proband_batch[idx + 1]["POS"]
        else:
            next_pos = -1000

        nearby = abs(r["POS"] - prev_pos) <= 3 or abs(r["POS"] - next_pos) <= 3
        checks = {
            "not_multiallelic": r["SAMPLES"]["TEST_SAMPLE"]["GT"]
            in ["0/1", "1/1", "1|0", "0|1", "1|1"],
            "hi_freq": (
                "GNOMAD_GENOMES" in r["INFO"]["ALL"]
                and r["INFO"]["ALL"]["GNOMAD_GENOMES"]["AF"][0] > 0.05
                and r["INFO"]["ALL"]["GNOMAD_GENOMES"]["AN"] > 5000
            ),
            "not_nearby": not nearby,
            "no_classification": not r["__HAS_CLASSIFICATION"],
        }
        if not all(checks.values()):
            included.append(r)
    assert included == total_prefiltered
    assert batch == total_batch


@ht.given(vcf_family_strategy(6))
@ht.settings(deadline=None, max_examples=100)  # A bit heavy, so few tests by default
def test_analysis_multiple(session, vcf_data):
    global ANALYSIS_NUM
    ANALYSIS_NUM += 1
    analysis_name = "TEST_ANALYSIS {}".format(ANALYSIS_NUM)

    vcf_string, ped_string, meta = vcf_data

    # Import generated analysis
    with tempinput(vcf_string) as vcf_file:
        with tempinput(ped_string or "") as ped_file:
            acd = AnalysisConfigData(
                vcf_file, analysis_name, "HBOCUTV", "v01", ped_path=ped_file if ped_string else None
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

    proband_variants = [v for v in meta["variants"] if "1" in v["samples"][0]["GT"]]
    no_coverage_samples = list()
    for idx, sample_name in enumerate(meta["sample_names"]):
        if all(tuple(v["samples"][idx]["GT"][::2]) == (".", ".") for v in meta["variants"]):
            no_coverage_samples.append(sample_name)

    # Start checking data
    # Samples
    proband_sample = None
    for sample_name, ped in meta["ped_info"].items():
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
        for variant in proband_variants:
            sample_data = {k: v for k, v in zip(meta["sample_names"], variant["samples"])}
            al = next(
                a
                for a in alleles
                if a.vcf_pos == variant["pos"]
                and a.vcf_ref == variant["ref"]
                and a.vcf_alt == variant["alt"]
                and a.chromosome == variant["chromosome"]
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
        for variant in meta["variants"]:
            for sample_name, sample_data in zip(meta["sample_names"], variant["samples"]):
                sample_allele_depth[sample_name].update(
                    {
                        k: v
                        for k, v in zip(
                            ["REF ({})".format(variant["ref"]), variant["alt"]],
                            [int(a) for a in sample_data["AD"].split(",")],
                        )
                    }
                )

        # Check that genotypesampledata is set correctly
        for key in ["allele", "secondallele"]:
            if key == "secondallele" and not fixtures[key]:
                continue
            for sample_name, data in fixtures[key]["sample_data"].items():
                gsd = fixtures[key]["genotypesampledata"][sample_name]
                if tuple(data["GT"][::2]) == ("1", "1"):
                    gsd_type = "Homozygous"
                elif tuple(data["GT"][::2]) in [("0", "1"), ("1", "0"), ("1", "."), (".", "1")]:
                    gsd_type = "Heterozygous"
                elif tuple(data["GT"][::2]) in [("0", "0"), ("0", "."), (".", "0")]:
                    gsd_type = "Reference"
                elif tuple(data["GT"][::2]) == (".", "."):
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
