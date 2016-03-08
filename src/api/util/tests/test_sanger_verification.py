import copy
import pytest
from ..sanger_verification import SangerVerification


@pytest.fixture
def pass_data():
    # Base data where all criterias should be met
    return {
        "changeFrom": "T",
        "changeTo": "C",
        "changeType": "SNP",
        "chromosome": "13",
        "genomeReference": "GRCh37",
        "genotype": {
            "alleleDepth": {
                "C": 50,
                "T": 53
            },
            "filterStatus": "PASS",
            "genotype": "T/C",
            "genotypeQuality": 99,
            "homozygous": False,
            "sequencingDepth": 106,
            "variantQuality": 5000
        },
        "openEndPosition": 32911756,
        "startPosition": 32911755
    }


class TestSangerVerification(object):

    def test_pass(self, pass_data):
        criterias = SangerVerification().check_criterias(pass_data)
        assert all(criterias.values())

    def test_filter_fail(self, pass_data):
        pass_data['genotype']['filterStatus'] = "."
        criterias = SangerVerification().check_criterias(pass_data)
        assert not criterias['FILTER']

    def test_qual_string_fail(self, pass_data):
        pass_data['genotype']['variantQuality'] = "STRING"
        criterias = SangerVerification().check_criterias(pass_data)
        assert not criterias['QUAL']

    def test_qual_low_fail(self, pass_data):
        pass_data['genotype']['variantQuality'] = 100
        criterias = SangerVerification().check_criterias(pass_data)
        assert not criterias['QUAL']

    def test_DP_fail(self, pass_data):
        pass_data['genotype']['sequencingDepth'] = 10
        criterias = SangerVerification().check_criterias(pass_data)
        assert not criterias['DP']

    def test_indel_fail(self, pass_data):
        # Test should fail if not a snp
        ref_indel = copy.deepcopy(pass_data)
        ref_indel['changeType'] = 'del'
        criterias = SangerVerification().check_criterias(ref_indel)
        assert not criterias['SNP']

        alt_indel = copy.deepcopy(pass_data)
        alt_indel['changeType'] = ['ins']
        criterias = SangerVerification().check_criterias(alt_indel)
        assert not criterias['SNP']

        both_indel = copy.deepcopy(pass_data)
        both_indel['changeType'] = ['indel']
        criterias = SangerVerification().check_criterias(both_indel)
        assert not criterias['SNP']

    def test_allele_depth(self, pass_data):

        hetero_high = copy.deepcopy(pass_data)
        hetero_high['genotype']['alleleDepth'] = {
            "C": 1,
            "T": 100
        }
        criterias = SangerVerification().check_criterias(hetero_high)
        assert not criterias['AD']

        hetero_low = copy.deepcopy(pass_data)
        hetero_low['genotype']['alleleDepth'] = {
            "C": 150,
            "T": 1
        }
        criterias = SangerVerification().check_criterias(hetero_low)
        assert not criterias['AD']

        homo_low = copy.deepcopy(pass_data)
        homo_low['genotype']['homozygous'] = True
        homo_low['genotype']['alleleDepth'] = {
            "C": 1,
            "T": 100
        }
        criterias = SangerVerification().check_criterias(homo_low)
        assert not criterias['AD']

        # Multi-allelic homo, ratio = 0.5 -> FAIL
        multi_homo_high = copy.deepcopy(pass_data)
        multi_homo_high['genotype']['homozygous'] = True
        multi_homo_high['genotype']['alleleDepth'] = {
            "C": 15,
            "T": 5,
            "G": 20
        }
        criterias = SangerVerification().check_criterias(multi_homo_high)
        assert not criterias['AD']

        # Multi-allelic hetero, ratio = 0.6 -> FAIL
        multi_hetero_high = copy.deepcopy(pass_data)
        multi_hetero_high['genotype']['alleleDepth'] = {
            "C": 15,
            "T": 5,
            "G": 30
        }
        criterias = SangerVerification().check_criterias(multi_hetero_high)
        assert not criterias['AD']
