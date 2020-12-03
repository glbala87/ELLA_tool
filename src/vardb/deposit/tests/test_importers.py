import vardb.deposit.importers as deposit
import hypothesis as ht
import hypothesis.strategies as st
from os.path import commonprefix


@st.composite
def positions(draw):
    def commonsuffix(strs):
        return commonprefix([s[::-1] for s in strs])[::-1]

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


@st.composite
def sequence(draw):
    return draw(st.text(alphabet=["A", "C", "G", "T"], min_size=1, max_size=4))


# Genotype import is tested as part of test_deposit


@ht.example(
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
@ht.example(
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
        "open_end_position": 41226488,
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
def test_allele_from_record(session, positions, manually_curated_result):

    chrom, pos, ref, alt = positions

    record = {
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

    allele_length = max(len(ref), len(alt))

    al = deposit.build_allele_from_record(record, ref_genome="GRCh37")
    if manually_curated_result:
        for k, v in manually_curated_result.items():
            assert al[k] == v

    expected_result = {
        "genome_reference": "GRCh37",
        "chromosome": chrom,
        "vcf_pos": pos,
        "vcf_ref": ref,
        "vcf_alt": alt,
        "length": 1,
    }

    if len(ref) == len(alt) == 1:
        expected_result.update(
            {
                "change_type": "SNP",
                "start_position": pos - 1,
                "open_end_position": pos,
                "change_from": ref,
                "change_to": alt,
                "length": allele_length,
            }
        )
    elif len(ref) >= 1 and len(alt) >= 1 and alt[0] != ref[0]:
        expected_result.update(
            {
                "change_type": "indel",
                "start_position": pos - 1,
                "open_end_position": pos - 1 + len(ref),
                "change_from": ref,
                "change_to": alt,
                "length": allele_length,
            }
        )
    elif len(ref) < len(alt):
        expected_result.update(
            {
                "change_type": "ins",
                "start_position": pos - 1,
                "open_end_position": pos,
                "change_from": "",
                "change_to": alt[1:],
                "length": allele_length - 1,
            }
        )
    elif len(ref) > len(alt):
        expected_result.update(
            {
                "change_type": "del",
                "start_position": pos,
                "open_end_position": pos + len(ref) - 1,
                "change_from": ref[1:],
                "change_to": "",
                "length": allele_length - 1,
            }
        )
    else:
        raise ValueError()

    assert al == expected_result


# SNP
@ht.example(("1", 123, "T", "C"), [("C", "CC")])  # => ("1", 122, "CTCC", "CCCC")
@ht.example(("1", 123, "A", "T"), [("AA", "T")])  # => ("1", 121, "AAAT", "AATT")
@ht.example(("1", 123, "T", "TT"), [("A", "")])  # => ("1", 122, "AT", "ATT")
# ins
@ht.example(("1", 123, "T", "TA"), [("C", "CC")])  # => ("1", 122, "CTCC", "CTACC")
@ht.example(("1", 123, "T", "TT"), [("C", "T")])  # => ("1", 122, "CTT", "CTTT")
# del
@ht.example(("1", 123, "CT", "C"), [("", "CC")])  # => ("1", 123, "CTCC", "CCC")
@ht.example(("1", 123, "TCAG", "T"), [("", "CAGCAG")])  # => ("1", 123, "TCAGCAGCAG", "TCAGCAG")
# indel
@ht.example(("1", 123, "CT", "AG"), [("AA", "")])  # => ("1", 121, "AACT", "AAAG")
@ht.example(("1", 123, "C", "AG"), [("", "AA")])  # => ("1", 123, "CAAA", "AGAAA")
@ht.example(("1", 123, "C", "AG"), [("AG", "AA")])  # => ("1", 121, "AGCAAA", "AGAGAAA")
@ht.given(
    st.one_of(positions()), st.lists(st.tuples(sequence(), sequence()), min_size=1, max_size=4)
)
def test_equivalent_vcf_representations(standard, padding):
    chrom, pos, ref, alt = standard
    equivalent = []
    for prefix, suffix in padding:
        N = len(prefix)
        equivalent.append((chrom, pos - N, prefix + ref + suffix, prefix + alt + suffix))

    positions = [standard] + equivalent

    assert len(positions) > 1
    items = []
    for position in positions:
        chrom, pos, ref, alt = position
        record = {
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
        item = deposit.build_allele_from_record(record, ref_genome="dabla")
        item.pop("vcf_pos")
        item.pop("vcf_ref")
        item.pop("vcf_alt")
        items.append(item)

    standard_item = items.pop(0)
    for x in items:
        assert x == standard_item


"""
@ht.example(
    {
        "CHROM": "1",
        "POS": 4185714,
        "ID": "DEL00000036",
        "REF": "C",
        "ALT": [
            "<DEL>"
        ],
        "QUAL": 317.0,
        "FILTER": "PASS",
        "INFO": {
            "ALL": {
                "SVTYPE": "DEL",
                "IMPRECISE": True,
                "SVMETHOD": "EMBL.DELLYv0.8.3",
                "END": 5583628,
                "PE": 7,
                "MAPQ": 45,
                "CT": "3to5",
                "CIPOS": [
                    -292,
                    292
                ],
                "CIEND": [
                    -292,
                    292
                ],
                "DELLY": True,
                "SVLEN": -1397914,
                "OCC_INDB_DELLY": 1,
                "FRQ_INDB_DELLY": 1.0,
                "OCC_INDB_MERGED": 1,
                "FRQ_INDB_MERGED": 1.0
            },
        },
        "SAMPLES": {
            "Diag-ValidationWGS2-HG002C2-PM": {
                "GT": "0/1",
                "GL": [
                    -18.4547,
                    0,
                    -208.755
                ],
                "GQ": 10000,
                "FT": "PASS",
                "RCL": 63639,
                "RC": 162842,
                "RCR": 83652,
                "CN": 2,
                "DR": 37,
                "DV": 7,
                "RR": 0,
                "RV": 0
            }
        }
    },
    {
        "chromosome": "1",
        "vcf_pos": 4185714,
        # "length": ...
        # "change_type": ...
    }
)
@ht.given(
#    st.one_of(positions()), st.lists(st.tuples(sequence(), sequence()), min_size=1, max_size=4)
)
"""


# def test_cnv_importer(session, record, expected_result):
# @ht.given(text())
@ht.example(
    {"CHROM": "1", "POS": 4185714, "ID": "DEL00000036", "REF": "C", "ALT": ["<DEL>"]},
    {"chromosome": "1"},
)
def parsedData():
    return {
        "CHROM": "1",
        "POS": 4185714,
        "ID": "DEL00000036",
        "REF": "C",
        "ALT": ["<DEL>"],
        "QUAL": 317.0,
        "FILTER": "PASS",
        "INFO": {
            "ALL": {
                "SVTYPE": "DEL",
                "IMPRECISE": True,
                "SVMETHOD": "EMBL.DELLYv0.8.3",
                "END": 5583628,
                "PE": 7,
                "MAPQ": 45,
                "CT": "3to5",
                "CIPOS": [-292, 292],
                "CIEND": [-292, 292],
                "DELLY": True,
                "SVLEN": -1397914,
                "OCC_INDB_DELLY": 1,
                "FRQ_INDB_DELLY": 1.0,
                "OCC_INDB_MERGED": 1,
                "FRQ_INDB_MERGED": 1.0,
            }
        },
        "SAMPLES": {
            "Diag-ValidationWGS2-HG002C2-PM": {
                "GT": "0/1",
                "GL": [-18.4547, 0, -208.755],
                "GQ": 10000,
                "FT": "PASS",
                "RCL": 63639,
                "RC": 162842,
                "RCR": 83652,
                "CN": 2,
                "DR": 37,
                "DV": 7,
                "RR": 0,
                "RV": 0,
            }
        },
    }


def test_cnv_importer(session):
    ai = deposit.AlleleImporter(session)
    allele = ai.add(parsedData())
    start_position = 4185713
    allele_length = 1397914
    end_position = start_position + allele_length

    assert start_position == allele["start_position"]
    assert allele_length == allele["length"]
    assert end_position == allele["open_end_position"]
