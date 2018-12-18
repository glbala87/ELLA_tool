import pytest
import vardb.deposit.importers as deposit


@pytest.fixture
def ref_genome():
    return "GRCh37"


@pytest.fixture
def allele_importer(session, ref_genome):
    return deposit.AlleleImporter(session, ref_genome=ref_genome)


# Genotype import is tested as part of test_deposit


class TestAlleleImporter:
    def test_snp(self, allele_importer, ref_genome):
        # Normal SNP
        allele_importer.add(
            {
                "ALT": ["A"],
                "CHROM": "17",
                "FILTER": ".",
                "ID": "H186",
                "INFO": {},
                "POS": 41226488,
                "QUAL": ".",
                "REF": "C",
                "SAMPLES": {"H01": {"GT": "0/1"}},
            }
        )
        al = allele_importer.process()[0]

        assert al["genome_reference"] == ref_genome
        assert al["chromosome"] == "17"
        assert al["start_position"] == 41226487
        assert al["open_end_position"] == 41226488
        assert al["change_from"] == "C"
        assert al["change_to"] == "A"
        assert al["change_type"] == "SNP"

    def test_insertion(self, allele_importer, ref_genome):
        allele_importer.add(
            {
                "ALT": ["CGCT"],
                "CHROM": "X",
                "FILTER": ".",
                "ID": "H186",
                "INFO": {},
                "POS": 41226488,
                "QUAL": ".",
                "REF": "C",
                "SAMPLES": {"H01": {"GT": "0/1"}},
            }
        )
        al = allele_importer.process()[0]

        assert al["genome_reference"] == ref_genome
        assert al["chromosome"] == "X"
        assert al["start_position"] == 41226488
        assert al["open_end_position"] == 41226491
        assert al["change_from"] == ""
        assert al["change_to"] == "GCT"
        assert al["change_type"] == "ins"

    def test_deletion(self, allele_importer, ref_genome):
        allele_importer.add(
            {
                "ALT": ["A"],
                "CHROM": "X",
                "FILTER": ".",
                "ID": "H186",
                "INFO": {},
                "POS": 41226488,
                "QUAL": ".",
                "REF": "AATATATT",
                "SAMPLES": {"H01": {"GT": "0/1"}},
            }
        )
        al = allele_importer.process()[0]

        assert al["genome_reference"] == ref_genome
        assert al["chromosome"] == "X"
        assert al["start_position"] == 41226488
        assert al["open_end_position"] == 41226495
        assert al["change_from"] == "ATATATT"
        assert al["change_to"] == ""
        assert al["change_type"] == "del"

    def test_indel(self, allele_importer, ref_genome):
        allele_importer.add(
            {
                "ALT": ["AGCT"],
                "CHROM": "X",
                "FILTER": ".",
                "ID": "H186",
                "INFO": {},
                "POS": 41226488,
                "QUAL": ".",
                "REF": "C",
                "SAMPLES": {"H01": {"GT": "0/1"}},
            }
        )
        al = allele_importer.process()[0]

        assert al["genome_reference"] == ref_genome
        assert al["chromosome"] == "X"
        assert al["start_position"] == 41226487
        assert al["open_end_position"] == 41226491
        assert al["change_from"] == "C"
        assert al["change_to"] == "AGCT"
        assert al["change_type"] == "indel"
