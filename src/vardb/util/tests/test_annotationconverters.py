# coding=utf-8
import pytest
from itertools import permutations
import re

from .. import annotationconverters


def test_get_pubmeds_HGMD():

    HGMD_EXTRAREFS_META = '##INFO=<ID=HGMD__extrarefs,Number=.,Type=String,Description="Format: (pmid|title|author|fullname|year|vol|issue|page|reftag|gene|disease|comments) (from /anno/data/variantDBs/HGMD/hgmd-2018.1_norm.vcf.gz)">'
    meta = {"INFO": [{"ID": "HGMD__extrarefs", "Description": HGMD_EXTRAREFS_META}]}
    data = {"HGMD__pmid": 1, "HGMD__extrarefs": "2|||||||||||,3|||||||||||"}

    pubmeds = annotationconverters.ConvertReferences().process(data, meta)
    pubmeds = annotationconverters.ConvertReferences().process(data)
    assert pubmeds[0] == {
        "pubmed_id": 1,
        "source": "HGMD",
        "source_info": "Primary literature report. No comments.",
    }

    assert pubmeds[1] == {
        "pubmed_id": 2,
        "source": "HGMD",
        "source_info": "Reftag not specified. No comments.",
    }

    assert pubmeds[2] == {
        "pubmed_id": 3,
        "source": "HGMD",
        "source_info": "Reftag not specified. No comments.",
    }


class TestFrequencyAnnotation:
    def test_gnomad_exomes_conversion(self):
        annotation_source = {
            "GNOMAD_EXOMES__AC_TEST": 13,
            "GNOMAD_EXOMES__AN_TEST": 2,
            "GNOMAD_EXOMES__AC_ZERO": 0,
            "GNOMAD_EXOMES__AN_ZERO": 0,
        }

        converted = annotationconverters.gnomad_exomes_frequencies(annotation_source)[
            "GNOMAD_EXOMES"
        ]
        assert "TEST" in converted["freq"]
        assert float(13) / 2 == converted["freq"]["TEST"]
        assert "ZERO" not in converted["freq"]

    def test_gnomad_genomes_conversion(self):
        annotation_source = {
            "GNOMAD_GENOMES__AC_TEST": 13,
            "GNOMAD_GENOMES__AN_TEST": 2,
            "GNOMAD_GENOMES__AC_ZERO": 0,
            "GNOMAD_GENOMES__AN_ZERO": 0,
        }

        converted = annotationconverters.gnomad_genomes_frequencies(annotation_source)[
            "GNOMAD_GENOMES"
        ]
        assert "TEST" in converted["freq"]
        assert float(13) / 2 == converted["freq"]["TEST"]
        assert "ZERO" not in converted["freq"]


CSQ_META = {
    "Description": "onsequence annotations from Ensembl VEP. Format: Allele|Consequence|IMPACT|SYMBOL|Gene|Feature_type|Feature|BIOTYPE|EXON|INTRON|HGVSc|HGVSp|cDNA_position|CDS_position|Protein_position|Amino_acids|Codons|Existing_variation|ALLELE_NUM|DISTANCE|STRAND|FLAGS|SYMBOL_SOURCE|HGNC_ID|CANONICAL|ENSP|REFSEQ_MATCH|SOURCE|GIVEN_REF|USED_REF|BAM_EDIT|SIFT|PolyPhen|DOMAINS|HGVS_OFFSET|HGVSg|CLIN_SIG|SOMATIC|PHENO|PUBMED|MOTIF_NAME|MOTIF_POS|HIGH_INF_POS|MOTIF_SCORE_CHANGE|RefSeq_gff|RefSeq_Interim_gff"
}
CSQ_KEYS = re.findall('Format: ([^"]*)', CSQ_META["Description"])[0].split("|")
CSQ_TEMPLATE = "|".join("{" + k + "}" for k in CSQ_KEYS)
BASE_CSQ_DATA = {
    **{k: "" for k in CSQ_KEYS},
    **{
        "Feature_type": "Transcript",
        "Feature": "NM_SOMETHING",
        "SYMBOL": "SomeSymbol",
        "HGNC_ID": 1100,
    },
}


def generate_raw_csq(modifications):
    csq_data = {**BASE_CSQ_DATA, **modifications}
    return CSQ_TEMPLATE.format(**csq_data)


class TestTranscriptAnnotation:
    def test_distance_computation(self):

        cases = [
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
        ]

        for hgvsc, exon_distance, coding_region_distance in cases:
            csq_modification = {"HGVSc": hgvsc}
            csq = annotationconverters.ConvertCSQ()(generate_raw_csq(csq_modification), CSQ_META)[0]
            assert csq["exon_distance"] == exon_distance, "{} failed {}!={}".format(
                hgvsc, csq["exon_distance"], exon_distance
            )
            assert (
                csq["coding_region_distance"] == coding_region_distance
            ), "{} failed {}!={}".format(
                hgvsc, csq["coding_region_distance"], coding_region_distance
            )

    def test_get_is_last_exon(self):
        csq_converter = annotationconverters.ConvertCSQ()
        assert (
            csq_converter(generate_raw_csq({"EXON": "20/20"}), CSQ_META)[0]["in_last_exon"] == "yes"
        )
        assert (
            csq_converter(generate_raw_csq({"EXON": "1/20"}), CSQ_META)[0]["in_last_exon"] == "no"
        )
        assert csq_converter(generate_raw_csq({}), CSQ_META)[0]["in_last_exon"] == "no"
        assert csq_converter(generate_raw_csq({}), CSQ_META)[0]["in_last_exon"] == "no"
        with pytest.raises(IndexError):
            csq_converter(generate_raw_csq({"EXON": "20__20"}), CSQ_META)

    def test_csq_transcripts(self):
        csq_converter = annotationconverters.ConvertCSQ()
        data = ",".join(
            [
                generate_raw_csq({"Feature": "NM_000090.3"}),
                generate_raw_csq({"Feature": "ENST123456"}),
                generate_raw_csq({"Feature": "NM_000091.2"}),
                generate_raw_csq({"Feature": "NOT_NM_OR_ENST__I_WILL_BE_FILTERED"}),
                generate_raw_csq({"Feature": "NotTranscript", "Feature_type": "Other"}),
            ]
        )

        transcripts = csq_converter(data, CSQ_META)

        # Only NM_ or ENST transcripts are included.
        assert len(transcripts) == 3
        assert transcripts[0]["transcript"] == "ENST123456"
        assert transcripts[1]["transcript"] == "NM_000090.3"
        assert transcripts[2]["transcript"] == "NM_000091.2"

    def test_hgnc_id_fetching(self):
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

        transcripts = annotationconverters.ConvertCSQ()(data, CSQ_META)

        assert len(transcripts) == 3
        assert transcripts[0]["transcript"] == "NM_000001.1"
        assert transcripts[0]["symbol"] == "BRCA1"
        assert transcripts[0]["hgnc_id"] == 1100
        assert transcripts[1]["transcript"] == "NM_000002.1"
        assert transcripts[1]["symbol"] == "BRCA1"
        assert transcripts[1]["hgnc_id"] == 1100
        assert transcripts[2]["transcript"] == "NM_000003.1"
        assert transcripts[2]["symbol"] == "BRCA2"
        assert transcripts[2]["hgnc_id"] == 1101

    def test_refseq_priority(self):
        # Test RefSeq priority

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
        csq_converter = annotationconverters.ConvertCSQ()
        for p in permutations(base):
            raw_csq = ",".join(generate_raw_csq(x) for x in p)
            transcripts = csq_converter(raw_csq, CSQ_META)
            assert len(transcripts) == 2
            assert transcripts[0]["transcript"] == "NM_000001.1"
            assert transcripts[0]["symbol"] == "RefSeq_gff"
            assert transcripts[1]["transcript"] == "NM_000002.1"

        # Remove top priority source
        base = [tx_data for tx_data in base if tx_data.get("SYMBOL") != "RefSeq_gff"]
        assert len(base) == 3
        raw_csq = ",".join(generate_raw_csq(x) for x in base)
        transcripts = csq_converter(raw_csq, CSQ_META)
        assert len(transcripts) == 2
        assert transcripts[0]["transcript"] == "NM_000001.1"
        assert transcripts[0]["symbol"] == "RefSeq_Interim_gff"
        assert transcripts[1]["transcript"] == "NM_000002.1"

        # Remove second top priority source
        base = [tx_data for tx_data in base if tx_data.get("SYMBOL") != "RefSeq_Interim_gff"]
        assert len(base) == 2
        raw_csq = ",".join(generate_raw_csq(x) for x in base)
        transcripts = csq_converter(raw_csq, CSQ_META)
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
    def test_long_variant_names(self, hgvsc, hgvsc_short, insertion):
        raw_csq = generate_raw_csq({"HGVSc": "NM_000000.1:" + hgvsc, "HGNC_ID": 1})
        converted = annotationconverters.ConvertCSQ()(raw_csq, CSQ_META)[0]
        assert converted["HGVSc"] == hgvsc
        assert converted["HGVSc_short"] == hgvsc_short
        assert converted.get("HGVSc_insertion") == insertion
