import copy
import pytest
from ..calculate_qc import genotype_calculate_qc


DEFAULT_ALLELE = {
    'vcf_ref': 'G',
    'vcf_alt': 'A',
    'change_type': 'SNP'
}

DEFAULT_GENOTYPE = {
    'sequencing_depth': 400,
    'variant_quality': 900,
    'multiallelic': False,
    'filter_status': 'PASS',
    'allele_depth': {
        'A': 100,
        'REF': 100
    },
    'type': 'Heterozygous'
}


@pytest.fixture
def genotype():
    return copy.deepcopy(DEFAULT_GENOTYPE)


@pytest.fixture
def allele():
    return copy.deepcopy(DEFAULT_ALLELE)


def test_allele_ratio_no_data(allele, genotype):
    genotype['allele_depth'] = {}
    assert 'allele_ratio' not in genotype_calculate_qc(allele, genotype, 'HTS')

    genotype['allele_depth'] = {
        'REF': 100
    }
    assert 'allele_ratio' not in genotype_calculate_qc(allele, genotype, 'HTS')


def test_allele_ratio_wrong_data_types(allele, genotype):
    genotype['allele_depth'] = {
        'A': None,
        'REF': 100
    }
    assert 'allele_ratio' not in genotype_calculate_qc(allele, genotype, 'HTS')

    allele['vcf_alt'] = 'G'  # vcf_alt not in allele_depth
    genotype['allele_depth'] = {
        'A': 100,
        'REF': 100
    }
    assert 'allele_ratio' not in genotype_calculate_qc(allele, genotype, 'HTS')


def test_allele_ratio_correct_calculations(allele, genotype):
    # Only zeros should give no ratio
    genotype['allele_depth'] = {
        'A': 0,
        'REF': 0
    }
    assert 'allele_ratio' not in genotype_calculate_qc(allele, genotype, 'HTS')

    genotype['allele_depth'] = {
        'A': 100,
        'REF': 100
    }
    assert genotype_calculate_qc(allele, genotype, 'HTS')['allele_ratio'] == 0.5

    genotype['allele_depth'] = {
        'A': 100,
        'REF': 0
    }
    assert genotype_calculate_qc(allele, genotype, 'HTS')['allele_ratio'] == 1


def test_needs_verification_checks_no_data(allele, genotype):
    allele['change_type'] = None
    genotype['allele_depth'] = None
    genotype['variant_quality'] = None
    genotype['sequencing_depth'] = None
    genotype['filter_status'] = None

    result = genotype_calculate_qc(allele, genotype, 'HTS')
    needs_verification_checks = result['needs_verification_checks']
    assert needs_verification_checks['snp'] is False
    assert needs_verification_checks['pass'] is False
    assert needs_verification_checks['qual'] is False
    assert needs_verification_checks['dp'] is False
    assert needs_verification_checks['allele_ratio'] is False
    assert needs_verification_checks['hts'] is True

    assert result['needs_verification'] is True


def test_needs_verification_positive(allele, genotype):

    # Heterozygous case
    allele['change_type'] = 'SNP'
    genotype['type'] = 'Heterozygous'
    genotype['allele_depth'] = {
        'A': 70,
        'REF': 50
    }
    genotype['variant_quality'] = 301
    genotype['sequencing_depth'] = 21
    genotype['filter_status'] = 'PASS'

    result = genotype_calculate_qc(allele, genotype, 'HTS')
    needs_verification_checks = result['needs_verification_checks']
    assert needs_verification_checks['snp'] is True
    assert needs_verification_checks['pass'] is True
    assert needs_verification_checks['qual'] is True
    assert needs_verification_checks['dp'] is True
    assert needs_verification_checks['allele_ratio'] is True
    assert needs_verification_checks['hts'] is True

    assert result['needs_verification'] is False

    # Homozygous case
    allele['change_type'] = 'SNP'
    genotype['type'] = 'Homozygous'
    genotype['allele_depth'] = {
        'A': 100,
        'REF': 10
    }
    genotype['variant_quality'] = 301
    genotype['sequencing_depth'] = 21
    genotype['filter_status'] = 'PASS'

    result = genotype_calculate_qc(allele, genotype, 'HTS')
    needs_verification_checks = result['needs_verification_checks']
    assert needs_verification_checks['snp'] is True
    assert needs_verification_checks['pass'] is True
    assert needs_verification_checks['qual'] is True
    assert needs_verification_checks['dp'] is True
    assert needs_verification_checks['allele_ratio'] is True
    assert needs_verification_checks['hts'] is True

    assert result['needs_verification'] is False


def test_needs_verification_hts_negative(allele, genotype):
    # Fail all checks, but sample type is Sanger
    allele['change_type'] = None
    genotype['allele_depth'] = None
    genotype['variant_quality'] = None
    genotype['sequencing_depth'] = None
    genotype['filter_status'] = None

    result = genotype_calculate_qc(allele, genotype, 'Sanger')
    needs_verification_checks = result['needs_verification_checks']
    assert needs_verification_checks['snp'] is False
    assert needs_verification_checks['pass'] is False
    assert needs_verification_checks['qual'] is False
    assert needs_verification_checks['dp'] is False
    assert needs_verification_checks['allele_ratio'] is False
    assert needs_verification_checks['hts'] is False

    assert result['needs_verification'] is False

def test_needs_verification_negative(allele, genotype):

    # Heterozygous case
    allele['change_type'] = 'indel'
    genotype['type'] = 'Heterozygous'
    genotype['allele_depth'] = {
        'A': 100,
        'REF': 1
    }
    genotype['variant_quality'] = 300
    genotype['sequencing_depth'] = 20
    genotype['filter_status'] = 'FAIL'

    result = genotype_calculate_qc(allele, genotype, 'HTS')
    needs_verification_checks = result['needs_verification_checks']
    assert needs_verification_checks['snp'] is False
    assert needs_verification_checks['pass'] is False
    assert needs_verification_checks['qual'] is False
    assert needs_verification_checks['dp'] is False
    assert needs_verification_checks['allele_ratio'] is False
    assert needs_verification_checks['hts'] is True

    assert result['needs_verification'] is True

    # Homozygous case
    allele['change_type'] = 'del'
    genotype['type'] = 'Homozygous'
    genotype['allele_depth'] = {
        'A': 50,
        'REF': 50
    }
    genotype['variant_quality'] = 0
    genotype['sequencing_depth'] = 0
    genotype['filter_status'] = 'something'

    result = genotype_calculate_qc(allele, genotype, 'HTS')
    needs_verification_checks = result['needs_verification_checks']
    assert needs_verification_checks['snp'] is False
    assert needs_verification_checks['pass'] is False
    assert needs_verification_checks['qual'] is False
    assert needs_verification_checks['dp'] is False
    assert needs_verification_checks['allele_ratio'] is False
    assert needs_verification_checks['hts'] is True

    assert result['needs_verification'] is True

    # One criteria fails
    allele['change_type'] = 'SNP'
    genotype['type'] = 'Homozygous'
    genotype['allele_depth'] = {
        'A': 100,
        'REF': 10
    }
    genotype['variant_quality'] = 301
    genotype['sequencing_depth'] = 20  # Fail
    genotype['filter_status'] = 'PASS'

    result = genotype_calculate_qc(allele, genotype, 'HTS')
    needs_verification_checks = result['needs_verification_checks']
    assert needs_verification_checks['snp'] is True
    assert needs_verification_checks['pass'] is True
    assert needs_verification_checks['qual'] is True
    assert needs_verification_checks['dp'] is False
    assert needs_verification_checks['allele_ratio'] is True
    assert needs_verification_checks['hts'] is True

    assert result['needs_verification'] is True
