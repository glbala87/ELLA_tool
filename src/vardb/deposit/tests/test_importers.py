import vardb.deposit.importers as deposit
import hypothesis as ht
import hypothesis.strategies as st
from os.path import commonprefix


@st.composite
def positions(draw):
    def commonsuffix(strs):
        return commonprefix([s[::-1] for s in strs])

    chrom = draw(st.sampled_from(["1", "2", "X"]))

    ref = draw(st.text(["A", "C", "G", "T"], min_size=1))
    alt = draw(st.text(["A", "C", "G", "T"], min_size=1))

    # Skew the selection away from indels (a threshold of 0.01 evens out the distribution between dels, ins and indels)
    r = draw(st.floats(min_value=0, max_value=1))
    ht.assume(r < 0.01 or (len(ref) == len(alt) == 1 or ref[0] == alt[0]))

    # Ignore variants with common suffix, e.g. g.123A<TA should be represented as g.122N<NT
    ht.assume(len(commonsuffix([ref, alt])) == 0)
    if len(commonprefix([ref, alt])) == 1:
        ht.assume(len(ref) == 1 or len(alt) == 1)
    else:
        ht.assume(len(commonprefix([ref, alt])) == 0)

    pos = draw(st.integers(min_value=1e4, max_value=1e7))
    return chrom, pos, ref, alt


# Genotype import is tested as part of test_deposit


ht.example(
    ("17", 41226488, "C", "A"),  # Normal SNP
    {
        "chromosome": "17",
        "change_type": "SNP",
        "start_position": 41226487,
        "open_end_position": 41226488,
        "change_from": "C",
        "change_to": "A",
    },
)
ht.example(
    ("11", 41226488, "C", "CGCT"),  # Three base insertion
    {
        "chromosome": "11",
        "change_type": "ins",
        "start_position": 41226487,
        "open_end_position": 41226488,
        "change_from": "",
        "change_to": "GCT",
    },
)


@ht.example(
    ("X", 41226488, "AATT", "A"),  # Three base deletion
    {
        "chromosome": "X",
        "change_type": "del",
        "start_position": 41226488,
        "open_end_position": 41226491,
        "change_from": "ATT",
        "change_to": "",
    },
)
@ht.example(
    ("14", 41226488, "C", "AGCT"),  # One base deleted, four bases inserted
    {
        "chromosome": "14",
        "change_type": "indel",
        "start_position": 41226487,
        "open_end_position": 41226491,
        "change_from": "C",
        "change_to": "AGCT",
    },
)
@ht.example(
    ("3", 41226488, "ACGT", "C"),  # Four bases deleted, one base inserted
    {
        "chromosome": "3",
        "change_type": "indel",
        "start_position": 41226487,
        "open_end_position": 41226491,
        "change_from": "ACGT",
        "change_to": "C",
    },
)
@ht.example(
    ("4", 41226488, "AT", "GC"),  # Two bases deleted, two bases inserted
    {
        "chromosome": "4",
        "change_type": "indel",
        "start_position": 41226487,
        "open_end_position": 41226489,
        "change_from": "AT",
        "change_to": "GC",
    },
)
@ht.given(st.one_of(positions()), st.just(None))
def test_dabla(session, positions, manually_curated_result):

    chrom, pos, ref, alt = positions

    allele_importer = deposit.AlleleImporter(session, ref_genome="GRCh37")
    allele_importer.add(
        {
            "ALT": [alt],
            "CHROM": chrom,
            "POS": pos,
            "REF": ref,
            "FILTER": ".",
            "ID": "H186",
            "INFO": {},
            "QUAL": ".",
            "SAMPLES": {"H01": {"GT": "0/1"}},
        }
    )

    al = allele_importer.process()[0]
    if manually_curated_result:
        for k, v in manually_curated_result.items():
            assert al[k] == v

    if len(ref) == len(alt) == 1:
        change_type = "SNP"
        start_position = pos - 1
        end_position = pos
        change_from = ref
        change_to = alt
    elif len(ref) >= 1 and len(alt) >= 1 and alt[0] != ref[0]:
        start_position = pos - 1
        end_position = pos - 1 + max(len(ref), len(alt))
        change_type = "indel"
        change_from = ref
        change_to = alt
    elif len(ref) < len(alt):
        start_position = pos - 1
        end_position = pos
        change_type = "ins"
        change_from = ""
        change_to = alt[1:]
    elif len(ref) > len(alt):
        start_position = pos
        end_position = pos + len(ref) - 1
        change_type = "del"
        change_from = ref[1:]
        change_to = ""
    else:
        raise ValueError()

    assert al["genome_reference"] == "GRCh37"
    assert al["chromosome"] == chrom
    assert al["start_position"] == start_position
    assert al["open_end_position"] == end_position
    assert al["change_from"] == change_from
    assert al["change_to"] == change_to
    assert al["change_type"] == change_type
