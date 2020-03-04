# coding=utf-8
import pytest
from itertools import permutations

from .. import annotationconverters
from .. import GNOMAD_EXOMES_RESULT_KEY, GNOMAD_EXOMES_ANNOTATION_KEY
from .. import GNOMAD_GENOMES_RESULT_KEY, GNOMAD_GENOMES_ANNOTATION_KEY
from .. import EXAC_RESULT_KEY, EXAC_ANNOTATION_KEY


class TestReferences:
    def test_get_pubmeds_HGMD(self):
        data = {"HGMD": {"pmid": 1, "extrarefs": [{"pmid": 2}, {"pmid": 3}]}}

        pubmeds = annotationconverters.ConvertReferences().process(data)
        assert pubmeds[0] == {
            "pubmed_id": 1,
            "sources": ["HGMD"],
            "source_info": {"HGMD": "Primary literature report. No comments."},
        }

        assert pubmeds[1] == {
            "pubmed_id": 2,
            "sources": ["HGMD"],
            "source_info": {"HGMD": "Reftag not specified. No comments."},
        }

        assert pubmeds[2] == {
            "pubmed_id": 3,
            "sources": ["HGMD"],
            "source_info": {"HGMD": "Reftag not specified. No comments."},
        }


class TestFrequencyAnnotation:
    def test_csq_no_gmaf(self):
        """
        Don't include GMAF if given for the REF allele only.
        """

        data = {"CSQ": [{"GMAF": {"C": 0.122}, "SAS_MAF": {"G": 0.123}, "Allele": "G"}]}
        freq = annotationconverters.csq_frequencies(data)
        assert "GMAF" not in freq["1000g"]["freq"]

    def test_frequency_strip_maf_from_name(self):
        """
        Don't include MAF part of name
        """
        data = {"CSQ": [{"GMAF": {"G": 0.122}, "EUR_MAF": {"G": 0.123}, "Allele": "G"}, {}]}
        freq = annotationconverters.csq_frequencies(data)
        assert "G" in freq["1000g"]["freq"]
        assert "GMAF" not in freq["1000g"]["freq"]
        assert "EUR" in freq["1000g"]["freq"]
        assert "EUR_MAF" not in freq["1000g"]["freq"]

    def test_exac_conversion(self):
        annotation_source = {
            EXAC_ANNOTATION_KEY: {"AC_TEST": [13], "AN_TEST": 2, "AC_ZERO": [0], "AN_ZERO": 0}
        }

        converted = annotationconverters.exac_frequencies(annotation_source)[EXAC_RESULT_KEY]
        assert "TEST" in converted["freq"]
        assert float(13) / 2 == converted["freq"]["TEST"]
        assert "ZERO" not in converted["freq"]

    def test_gnomad_exomes_conversion(self):

        annotation_source = {
            GNOMAD_EXOMES_ANNOTATION_KEY: {
                "AC_TEST": [13],
                "AN_TEST": 2,
                "AC_ZERO": [0],
                "AN_ZERO": 0,
            }
        }

        converted = annotationconverters.gnomad_exomes_frequencies(annotation_source)[
            GNOMAD_EXOMES_RESULT_KEY
        ]
        assert "TEST" in converted["freq"]
        assert float(13) / 2 == converted["freq"]["TEST"]
        assert "ZERO" not in converted["freq"]

    def test_gnomad_genomes_conversion(self):

        annotation_source = {
            GNOMAD_GENOMES_ANNOTATION_KEY: {
                "AC_TEST": [13],
                "AN_TEST": 2,
                "AC_ZERO": [0],
                "AN_ZERO": 0,
            }
        }

        converted = annotationconverters.gnomad_genomes_frequencies(annotation_source)[
            GNOMAD_GENOMES_RESULT_KEY
        ]
        assert "TEST" in converted["freq"]
        assert float(13) / 2 == converted["freq"]["TEST"]
        assert "ZERO" not in converted["freq"]

    def test_exac_hom_count_inclusion(self):
        annotation_source = {"EXAC": {"Hom_TEST": [13]}}

        converted = annotationconverters.exac_frequencies(annotation_source)[EXAC_RESULT_KEY]
        assert "TEST" in converted["hom"]
        assert 13 == converted["hom"]["TEST"]

    def test_esp_hom_count_inclusion(self):

        data = {"CSQ": [{"EA_MAF": {"G": 0.122}, "AA_MAF": {"G": 0.123}, "Allele": "G"}, {}]}

        freqs = annotationconverters.csq_frequencies(data)
        assert 0.122 == freqs["esp6500"]["freq"]["EA"]
        assert 0.123 == freqs["esp6500"]["freq"]["AA"]


class TestTranscriptAnnotation:
    def test_distance_computation(self):
        def generate_data(hgvsc):
            return {
                "CSQ": [
                    {
                        "Feature_type": "Transcript",
                        "HGVSc": hgvsc,
                        "Feature": "NM_SOMETHING",
                        "SYMBOL": "SomeSymbol",
                        "HGNC_ID": 1,
                    }
                ]
            }

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
            csq = annotationconverters.ConvertCSQ()(generate_data(hgvsc))[0]
            assert csq["exon_distance"] == exon_distance, "{} failed {}!={}".format(
                hgvsc, csq["exon_distance"], exon_distance
            )
            assert (
                csq["coding_region_distance"] == coding_region_distance
            ), "{} failed {}!={}".format(
                hgvsc, csq["coding_region_distance"], coding_region_distance
            )

    def test_get_is_last_exon(self):
        def generate_data(additions):
            data = {
                "CSQ": [
                    {
                        "Feature_type": "Transcript",
                        "Feature": "NM_SOMETHING",
                        "SYMBOL": "SomeSymbol",
                        "HGNC_ID": 1,
                    }
                ]
            }
            data["CSQ"][0].update(additions)
            return data

        csq_converter = annotationconverters.ConvertCSQ()
        assert csq_converter(generate_data({"EXON": "20/20"}))[0]["in_last_exon"] == "yes"
        assert csq_converter(generate_data({"EXON": "1/20"}))[0]["in_last_exon"] == "no"
        assert csq_converter(generate_data({}))[0]["in_last_exon"] == "no"
        assert csq_converter(generate_data({}))[0]["in_last_exon"] == "no"
        with pytest.raises(IndexError):
            csq_converter(generate_data({"EXON": "20__20"}))

    def test_csq_transcripts(self):
        csq_converter = annotationconverters.ConvertCSQ()
        data = {
            "CSQ": [
                {"Feature": "NM_000090.3", "HGNC_ID": 1100, "Feature_type": "Transcript"},
                {"Feature": "ENST123456", "HGNC_ID": 1100, "Feature_type": "Transcript"},
                {"Feature": "NM_000091.2", "HGNC_ID": 1100, "Feature_type": "Transcript"},
                {
                    "Feature": "NOT_NM_OR_ENST__I_WILL_BE_FILTERED",
                    "HGNC_ID": 1100,
                    "Feature_type": "Transcript",
                },
                {"Feature": "NotTranscript", "HGNC_ID": 1100, "Feature_type": "Other"},
            ]
        }

        transcripts = csq_converter(data)

        # Only NM_ or ENST transcripts are included.
        assert len(transcripts) == 3
        assert transcripts[0]["transcript"] == "ENST123456"
        assert transcripts[1]["transcript"] == "NM_000090.3"
        assert transcripts[2]["transcript"] == "NM_000091.2"

        # Test HGNC ID fetching
        data = {
            "CSQ": [
                {
                    "Feature": "NM_000000.1",
                    "Gene": "GENE_WITHOUT_HGNC_ID",
                    "Feature_type": "Transcript",
                },
                {
                    "Feature": "NM_000001.1",
                    "SYMBOL": "BRCA1",
                    "Feature_type": "Transcript",
                },  # Will fetch HGNC id from symbol
                {
                    "Feature": "NM_000002.1",
                    "Gene": "672",
                    "Feature_type": "Transcript",
                },  # Will fetch HGNC id from Gene (NCBI gene id 672 = BRCA1)
                {
                    "Feature": "NM_000003.1",
                    "Gene": "ENSG00000139618",
                    "Feature_type": "Transcript",
                },  # Will fetch HGNC id from Gene (NCBI gene id ENSG00000139618 = BRCA2)
            ]
        }

        transcripts = csq_converter(data)
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

        # Test RefSeq priority
        data = {
            "CSQ": [
                {
                    "Feature": "NM_000001.1",
                    "SYMBOL": "RefSeq",
                    "HGNC_ID": 1100,
                    "Feature_type": "Transcript",
                    "SOURCE": "RefSeq",
                },
                {
                    "Feature": "NM_000001.1",
                    "SYMBOL": "RefSeq_Interim_gff",
                    "HGNC_ID": 1100,
                    "Feature_type": "Transcript",
                    "SOURCE": "RefSeq_Interim_gff",
                },
                {
                    "Feature": "NM_000001.1",
                    "SYMBOL": "RefSeq_gff",
                    "HGNC_ID": 1100,
                    "Feature_type": "Transcript",
                    "SOURCE": "RefSeq_gff",
                },
                {
                    "Feature": "NM_000002.1",
                    "HGNC_ID": 1100,
                    "Feature_type": "Transcript",
                },  # Different transcript, should not affect priority
            ]
        }

        # Order shouldn't matter, check all 4!=24 permutations
        for p in permutations(data["CSQ"]):
            transcripts = csq_converter({"CSQ": p})
            assert len(transcripts) == 2
            assert transcripts[0]["transcript"] == "NM_000001.1"
            assert transcripts[0]["symbol"] == "RefSeq_gff"
            assert transcripts[1]["transcript"] == "NM_000002.1"

        # Remove top priority source
        data["CSQ"] = [tx_data for tx_data in data["CSQ"] if tx_data.get("SYMBOL") != "RefSeq_gff"]
        assert len(data["CSQ"]) == 3
        transcripts = csq_converter(data)
        assert len(transcripts) == 2
        assert transcripts[0]["transcript"] == "NM_000001.1"
        assert transcripts[0]["symbol"] == "RefSeq_Interim_gff"
        assert transcripts[1]["transcript"] == "NM_000002.1"

        # Remove second top priority source
        data["CSQ"] = [
            tx_data for tx_data in data["CSQ"] if tx_data.get("SYMBOL") != "RefSeq_Interim_gff"
        ]
        assert len(data["CSQ"]) == 2
        transcripts = csq_converter(data)
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
        def generate_data(hgvsc):
            transcript = "NM_007294.3"
            return {
                "CSQ": [
                    {
                        "Feature_type": "Transcript",
                        "Feature": transcript,
                        "HGNC_ID": 1,
                        "SYMBOL": "SomeGeneSymbol",
                        "HGVSc": transcript + ":" + hgvsc,
                    }
                ]
            }

        converted = annotationconverters.ConvertCSQ()(generate_data(hgvsc))[0]
        assert converted["HGVSc"] == hgvsc
        assert converted["HGVSc_short"] == hgvsc_short
        assert converted.get("HGVSc_insertion") == insertion
