from itertools import permutations
import re
from typing import Any
import pytest
from vardb.deposit.annotationconverters.vepconverter import VEPConverter

CSQ_META = {
    "Description": "onsequence annotations from Ensembl VEP. Format: Allele|Consequence|IMPACT|SYMBOL|Gene|Feature_type|Feature|BIOTYPE|EXON|INTRON|HGVSc|HGVSp|cDNA_position|CDS_position|Protein_position|Amino_acids|Codons|Existing_variation|ALLELE_NUM|DISTANCE|STRAND|FLAGS|SYMBOL_SOURCE|HGNC_ID|CANONICAL|ENSP|REFSEQ_MATCH|SOURCE|GIVEN_REF|USED_REF|BAM_EDIT|SIFT|PolyPhen|DOMAINS|HGVS_OFFSET|HGVSg|CLIN_SIG|SOMATIC|PHENO|PUBMED|MOTIF_NAME|MOTIF_POS|HIGH_INF_POS|MOTIF_SCORE_CHANGE|RefSeq_gff|RefSeq_Interim_gff"
}
CSQ_KEYS = re.findall('Format: ([^"]*)', CSQ_META["Description"])[0].split("|")
CSQ_TEMPLATE = "|".join("{" + k + "}" for k in CSQ_KEYS)
BASE_CSQ_DATA: Any = {
    **{k: "" for k in CSQ_KEYS},
    **{
        "Feature_type": "Transcript",
        "Feature": "NM_SOMETHING",
        "SYMBOL": "SomeSymbol",
        "HGNC_ID": 1100,
        "STRAND": 1,
    },
}


def generate_raw_csq(modifications):
    csq_data = {**BASE_CSQ_DATA, **modifications}
    return CSQ_TEMPLATE.format(**csq_data)


@pytest.mark.parametrize(
    "hgvsc,expected_exon_distance,expected_coding_region_distance",
    [
        ("NM_007294.3:c.4535-213G>T", -213, None),
        ("NM_007294.3:c.4535+213G>T", 213, None),
        ("NM_007294.3:c.*35-21G>T", -21, None),
        ("NM_007294.3:c.-35+21G>T", 21, None),
        ("ENST123123:c.4535+1insAAA", 1, None),
        ("ENST123123:c.4535-1dupTTT", -1, None),
        ("ENST123123:c.4535+0dupTTT", 0, 0),
        ("ENST123123:n.4535+1insAAA", 1, None),
        ("ENST123123:n.4535-1dupTTT", -1, None),
        ("ENST123123:c.4535G>T", 0, 0),
        ("NM_007294.3:c.4535G>T", 0, 0),
        ("ENST123123:n.4535G>T", 0, 0),
        ("NM_007294.3:n.4535G>T", 0, 0),
        ("NM_007294.3:c.*4535G>T", 0, 4535),
        ("NM_007294.3:c.-4535G>T", 0, -4535),
        ("NM_007294.3:c.820-131_820-130delAA", -130, None),
        ("NM_007294.3:n.1901_1904delAAGT", 0, 0),
        ("NM_007294.3:c.248-1_248insA", 0, 0),
        ("NM_007294.3:c.248+1_248insA", 0, 0),
        ("NM_007294.3:c.248_248-1insA", 0, 0),
        ("NM_007294.3:c.248_248+1insA", 0, 0),
        ("NM_007294.3:c.-315_-314delAC", 0, -314),
        ("NM_007294.3:c.-264+88_-264+89delTT", 88, None),
        ("NM_007294.3:c.-264-89_-264-88delTT", -88, None),
        ("NM_007294.3:c.*264+88_*264+89delTT", 88, None),
        ("NM_007294.3:c.*264-89_*264-88delTT", -88, None),
        ("NM_007294.3:c.1597-10_1597-3dupTTATTTAT", -3, None),
        ("NM_007294.3:c.13+6_14-8dupTTATTTAT", 6, None),
        ("NM_007294.3:c.13-6_14+8dupTTATTTAT", -6, None),
        ("NM_007294.3:c.13-8_14+6dupTTATTTAT", 6, None),
        ("NM_007294.3:c.13+8_14-6dupTTATTTAT", -6, None),
        ("NM_007294.3:c.*13+6_*14-8dupTTATTTAT", 6, None),
        ("NM_007294.3:c.*13-6_*14+8dupTTATTTAT", -6, None),
        ("NM_007294.3:c.*13-8_*14+6dupTTATTTAT", 6, None),
        ("NM_007294.3:c.*13+8_*14-6dupTTATTTAT", -6, None),
        ("NM_007294.3:c.-13+6_-14-8dupTTATTTAT", 6, None),
        ("NM_007294.3:c.-13-6_-14+8dupTTATTTAT", -6, None),
        ("NM_007294.3:c.-13-8_-14+6dupTTATTTAT", 6, None),
        ("NM_007294.3:c.-13+8_-14-6dupTTATTTAT", -6, None),
        ("NM_007294.3:c.*13+6_*14-8dupTTATTTAT", 6, None),
        ("NM_007294.3:c.*13-6_*14+8dupTTATTTAT", -6, None),
        ("NM_007294.3:c.*13-8_*14+6dupTTATTTAT", 6, None),
        ("NM_007294.3:c.*13+8_*14-6dupTTATTTAT", -6, None),
        ("NM_007294.3:c.-13+6_-14-8dupTTATTTAT", 6, None),
        ("NM_007294.3:c.-13-6_-14+8dupTTATTTAT", -6, None),
        ("NM_007294.3:c.-13-8_-14+6dupTTATTTAT", 6, None),
        ("NM_007294.3:c.-13+8_-14-6dupTTATTTAT", -6, None),
        ("NM_007294.3:c.*1+6_8dupTTATTTAT", 0, 0),
        ("NM_007294.3:c.*1-6_8dupTTATTTAT", 0, 0),
        ("NM_007294.3:c.-1-8_6dupTTATTTAT", 0, 0),
        ("NM_007294.3:c.-1+8_6dupTTATTTAT", 0, 0),
        ("NM_007294.3:c.6_-1+8dupTTATTTAT", 0, 0),
        ("NM_007294.3:c.6_-1-8dupTTATTTAT", 0, 0),
        ("NM_007294.3:c.8_*1-6dupTTATTTAT", 0, 0),
        ("NM_007294.3:c.8_*1+6dupTTATTTAT", 0, 0),
        ("NM_007294.3:c.248+3_249-8del", 3, None),
        ("NM_007294.3:c.248-3_249+8del", -3, None),
        ("NM_007294.3:c.248+8_249-3del", -3, None),
        ("NM_007294.3:c.248-8_249+3del", 3, None),
        ("NM_007294.3:c.*-15A>C", None, None),  # Illegal
    ],
)
def test_distance_computation(hgvsc, expected_exon_distance, expected_coding_region_distance):

    converter = VEPConverter(CSQ_META, None)
    converter.setup()
    raw_csq = generate_raw_csq({"HGVSc": hgvsc})
    processed = converter(raw_csq)
    assert len(processed) == 1
    assert processed[0]["exon_distance"] == expected_exon_distance
    assert processed[0]["coding_region_distance"] == expected_coding_region_distance


def test_get_is_last_exon():
    converter = VEPConverter(CSQ_META, None)
    converter.setup()

    raw_csq = generate_raw_csq({"EXON": "20/20"})
    processed = converter(raw_csq)
    assert len(processed) == 1
    assert processed[0]["in_last_exon"] == "yes"

    raw_csq = generate_raw_csq({"EXON": "19/20"})
    processed = converter(raw_csq)
    assert len(processed) == 1
    assert processed[0]["in_last_exon"] == "no"

    raw_csq = generate_raw_csq({})
    processed = converter(raw_csq)
    assert len(processed) == 1
    assert processed[0]["in_last_exon"] == "no"

    raw_csq = generate_raw_csq({"EXON": "20__20"})
    with pytest.raises(IndexError):
        converter(raw_csq)


def test_csq_transcripts():
    converter = VEPConverter(CSQ_META, None)
    converter.setup()
    data = ",".join(
        [
            generate_raw_csq({"Feature": "NM_000090.3"}),
            generate_raw_csq({"Feature": "ENST123456"}),
            generate_raw_csq({"Feature": "NM_000091.2"}),
            generate_raw_csq({"Feature": "NOT_NM_OR_ENST__I_WILL_BE_FILTERED"}),
            generate_raw_csq({"Feature": "NM_foobar", "Feature_type": "Other"}),
        ]
    )

    processed = converter(data)

    # Only NM_ or ENST transcripts are included.
    assert len(processed) == 3
    assert processed[0]["transcript"] == "ENST123456"
    assert processed[1]["transcript"] == "NM_000090.3"
    assert processed[2]["transcript"] == "NM_000091.2"


def test_hgnc_id_fetching():
    converter = VEPConverter(CSQ_META, None)
    converter.setup()
    data = ",".join(
        [
            generate_raw_csq(
                {"Feature": "NM_000000.1", "Gene": "GENE_WITHOUT_HGNC_ID", "HGNC_ID": ""}
            ),
            generate_raw_csq(
                {"Feature": "NM_000001.1", "SYMBOL": "BRCA1", "HGNC_ID": ""}
            ),  # Will fetch HGNC id from symbol
            generate_raw_csq(
                {"Feature": "NM_000002.1", "Gene": "672", "HGNC_ID": "", "SYMBOL": ""}
            ),  # Will fetch HGNC id from Gene (NCBI gene id 672 = BRCA1)
            generate_raw_csq(
                {
                    "Feature": "NM_000003.1",
                    "Gene": "ENSG00000139618",
                    "HGNC_ID": "",
                    "SYMBOL": "",
                }
            ),  # Will fetch HGNC id from Gene (NCBI gene id ENSG00000139618 = BRCA2)
        ]
    )

    processed = converter(data)

    assert len(processed) == 3
    assert processed[0]["transcript"] == "NM_000001.1"
    assert processed[0]["symbol"] == "BRCA1"
    assert processed[0]["hgnc_id"] == 1100
    assert processed[1]["transcript"] == "NM_000002.1"
    assert processed[1]["symbol"] == "BRCA1"
    assert processed[1]["hgnc_id"] == 1100
    assert processed[2]["transcript"] == "NM_000003.1"
    assert processed[2]["symbol"] == "BRCA2"
    assert processed[2]["hgnc_id"] == 1101


def test_refseq_priority():
    converter = VEPConverter(CSQ_META, None)
    converter.setup()

    base = [
        {
            "Feature": "NM_000001.1",
            "SYMBOL": "RefSeq",
            "Feature_type": "Transcript",
            "SOURCE": "RefSeq",
        },
        {
            "Feature": "NM_000001.1",
            "SYMBOL": "RefSeq_Interim_gff",
            "Feature_type": "Transcript",
            "SOURCE": "RefSeq_Interim_gff",
        },
        {
            "Feature": "NM_000001.1",
            "SYMBOL": "RefSeq_gff",
            "Feature_type": "Transcript",
            "SOURCE": "RefSeq_gff",
        },
        {
            "Feature": "NM_000002.1",
            "Feature_type": "Transcript",
        },  # Different transcript, should not affect priority
    ]

    # Order shouldn't matter, check all 4!=24 permutations
    for p in permutations(base):
        raw_csq = ",".join(generate_raw_csq(x) for x in p)
        transcripts = converter(raw_csq)
        assert len(transcripts) == 2
        assert transcripts[0]["transcript"] == "NM_000001.1"
        assert transcripts[0]["symbol"] == "RefSeq_gff"
        assert transcripts[1]["transcript"] == "NM_000002.1"

    # Remove top priority source
    base = [tx_data for tx_data in base if tx_data.get("SYMBOL") != "RefSeq_gff"]
    assert len(base) == 3
    raw_csq = ",".join(generate_raw_csq(x) for x in base)
    transcripts = converter(raw_csq)
    assert len(transcripts) == 2
    assert transcripts[0]["transcript"] == "NM_000001.1"
    assert transcripts[0]["symbol"] == "RefSeq_Interim_gff"
    assert transcripts[1]["transcript"] == "NM_000002.1"

    # Remove second top priority source
    base = [tx_data for tx_data in base if tx_data.get("SYMBOL") != "RefSeq_Interim_gff"]
    assert len(base) == 2
    raw_csq = ",".join(generate_raw_csq(x) for x in base)
    transcripts = converter(raw_csq)
    assert len(transcripts) == 2
    assert transcripts[0]["transcript"] == "NM_000001.1"
    assert transcripts[0]["symbol"] == "RefSeq"
    assert transcripts[1]["transcript"] == "NM_000002.1"


@pytest.mark.parametrize(
    "hgvsc,hgvsc_short,insertion",
    [
        ("c.4416-77_4416-48delCTCTTCTCTTCTCTTCTCTTCTCTTCTCTT", "c.4416-77_4416-48del", None),
        ("c.123_133dupCGACGACGCAG", "c.123_133dup", None),
        ("c.131_132insACTTGCTGCTT", "c.131_132ins(11)", "ACTTGCTGCTT"),
        ("c.123_133delCGACGACGCAGinsACTTGCTGCTT", "c.123_133delins(11)", "ACTTGCTGCTT"),
        ("c.123_124delCGinsACTTGCTGCTT", "c.123_124delCGins(11)", "ACTTGCTGCTT"),
    ],
)
def test_long_variant_names(hgvsc, hgvsc_short, insertion):
    converter = VEPConverter(CSQ_META, None)
    converter.setup()
    raw_csq = generate_raw_csq({"HGVSc": "NM_000000.1:" + hgvsc, "HGNC_ID": 1})
    processed = converter(raw_csq)
    assert len(processed) == 1
    assert processed[0]["HGVSc"] == hgvsc
    assert processed[0]["HGVSc_short"] == hgvsc_short
    assert processed[0].get("HGVSc_insertion") == insertion
