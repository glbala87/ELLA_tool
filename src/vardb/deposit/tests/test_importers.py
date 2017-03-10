import pytest
import mock

import vardb.deposit.importers as deposit
from vardb.datamodel import sample, allele


class SessionMock(mock.Mock):

    def add(self, obj):
        print "Added:", obj

    def one(self):
        return self

    def all(self):
        return []

    def __getattr__(self, key):
        if key not in ['one', 'all']:
            return self
        else:
            return super(SessionMock, self).__getattr__(key)


@pytest.fixture
def session():
    s = SessionMock()
    return s


@pytest.fixture
def ref_genome():
    return 'GRCh37'


@pytest.fixture
def genotype_importer(session):
    return deposit.GenotypeImporter(session)


@pytest.fixture
def allele_importer(session, ref_genome):
    return deposit.AlleleImporter(session, ref_genome=ref_genome)


def test_anno_diff():
    assert not deposit.AnnotationImporter.diff_annotation({'b': 2, 'a': 1}, {'a': 1, 'b': 2})
    assert not deposit.AnnotationImporter.diff_annotation({'a': 1, 'b': [1,2,3]}, {'a': 1, 'b': [1,2,3]})
    # element order in list does matter:
    assert deposit.AnnotationImporter.diff_annotation({'a': 1, 'b': [1,2,3]}, {'a': 1, 'b': [3,2,1]})

    # element order in list does *not* matter when looking at the CSQ element:
    assert not deposit.AnnotationImporter.diff_annotation({'a': 1, 'CSQ': [1,2,3]}, {'a': 1, 'CSQ': [3,2,1]})

class TestGenotypeImporter():

    def test_genotype(self, genotype_importer):

        db_alleles = [allele.Allele(), allele.Allele()]
        db_sample = sample.Sample()
        db_analysis = sample.Analysis()
        samples1 = {
            'TEST_1': {
                'GT': '0/1'
            },
            'TEST_2': {
                'GT': '1|1',
                'GQ': 234.4,
                'DP': 12
            },
            'TEST_3': {
                'GT': './1',
                'GQ': 234.4,
                'DP': 12
            }

        }
        samples2={
            'TEST_1': {
                'GT': '0/0'
            },
            'TEST_2': {
                'GT': '0|0',
                'GQ': 234.4,
                'DP': 12
            },
            'TEST_3': {
                'GT': '1/.',
                'GQ': 234.4,
                'DP': 12
            }

        }



        data1 = [{
                'QUAL': '.',
                'ID': 'H186',
                'POS': 1234,
                'REF': 'T',
                'ALT': 'A',
                'FILTER': 'PASS',
                'SAMPLES': samples1
            },
            {
                'QUAL': '.',
                'ID': 'H186',
                'POS': 1234,
                'REF': 'T',
                'ALT': 'G',
                'FILTER': 'PASS',
                'SAMPLES': samples2
            },
        ]


        result1 = genotype_importer.process(data1, 'TEST_1', db_analysis, db_sample, db_alleles)

        assert result1.allele == db_alleles[0]
        # Second allele will only be set if heterozygous non-ref
        assert result1.secondallele is None
        assert result1.homozygous is False
        assert result1.sample == db_sample
        assert result1.genotype_quality is None
        assert result1.sequencing_depth is None
        assert result1.variant_quality is None

        data2 = [{
                'QUAL': 456,
                'ID': 'H186',
                'POS': 1234,
                'REF': 'T',
                'ALT': 'A',
                'FILTER': 'PASS',
                'SAMPLES': samples1
            },
            {
                'QUAL': 456,
                'ID': 'H186',
                'POS': 1234,
                'REF': 'T',
                'ALT': 'G',
                'FILTER': 'PASS',
                'SAMPLES': samples2
            }
        ]

        result2 = genotype_importer.process(data2, 'TEST_2', db_analysis, db_sample, db_alleles)

        assert result2.allele == db_alleles[0]
        assert result2.secondallele is None
        assert result2.homozygous is True
        assert result2.sample == db_sample
        assert result2.genotype_quality == 234.4
        assert result2.sequencing_depth == 12
        assert result2.variant_quality == 456

        data3=[{
                'QUAL': 456,
                'ID': 'H186',
                'POS': 1234,
                'REF': 'T',
                'ALT': 'A',
                'FILTER': 'PASS',
                'SAMPLES': samples1
            },
            {
                'QUAL': 456,
                'ID': 'H186',
                'POS': 1234,
                'REF': 'T',
                'ALT': 'G',
                'FILTER': 'PASS',
                'SAMPLES': samples2
            }
        ]

        result3 = genotype_importer.process(data3, 'TEST_3', db_analysis, db_sample, db_alleles)
        assert result3.allele == db_alleles[1]
        assert result3.secondallele == db_alleles[0]
        assert result3.homozygous is False
        assert result3.sample == db_sample
        assert result3.genotype_quality == 234.4
        assert result3.sequencing_depth == 12
        assert result3.variant_quality == 456


class TestAlleleImporter():

    def test_snp(self, allele_importer, ref_genome):
        # Normal SNP
        allele = allele_importer.process({
            'ALT': ['A'],
            'CHROM': '17',
            'FILTER': '.',
            'ID': 'H186',
            'INFO': {},
            'POS': 41226488,
            'QUAL': '.',
            'REF': 'C',
            'SAMPLES': {'H01': {'GT': '0/1'}}
        })[0]

        assert allele.genome_reference == ref_genome
        assert allele.chromosome == '17'
        assert allele.start_position == 41226487
        assert allele.open_end_position == 41226488
        assert allele.change_from == 'C'
        assert allele.change_to == 'A'
        assert allele.change_type == 'SNP'

    def test_multi_snp(self, allele_importer, ref_genome):
        al1, al2 = allele_importer.process({
            'ALT': ['A', 'G'],
            'CHROM': '17',
            'FILTER': '.',
            'ID': 'H186',
            'INFO': {},
            'POS': 41226488,
            'QUAL': '.',
            'REF': 'C',
            'SAMPLES': {'H01': {'GT': '0/1'}}
        })

        assert al1.genome_reference == ref_genome
        assert al1.chromosome == '17'
        assert al1.start_position == 41226487
        assert al1.open_end_position == 41226488
        assert al1.change_from == 'C'
        assert al1.change_to == 'A'
        assert al1.change_type == 'SNP'

        assert al2.genome_reference == ref_genome
        assert al2.chromosome == '17'
        assert al2.start_position == 41226487
        assert al2.open_end_position == 41226488
        assert al2.change_from == 'C'
        assert al2.change_to == 'G'
        assert al2.change_type == 'SNP'

    def test_insertion(self, allele_importer, ref_genome):
        al = allele_importer.process({
            'ALT': ['CGCT'],
            'CHROM': 'X',
            'FILTER': '.',
            'ID': 'H186',
            'INFO': {},
            'POS': 41226488,
            'QUAL': '.',
            'REF': 'C',
            'SAMPLES': {'H01': {'GT': '0/1'}}
        })[0]

        assert al.genome_reference == ref_genome
        assert al.chromosome == 'X'
        assert al.start_position == 41226488
        assert al.open_end_position == 41226491
        assert al.change_from == ''
        assert al.change_to == 'GCT'
        assert al.change_type == 'ins'

    def test_deletion(self, allele_importer, ref_genome):
        al = allele_importer.process({
            'ALT': ['A'],
            'CHROM': 'X',
            'FILTER': '.',
            'ID': 'H186',
            'INFO': {},
            'POS': 41226488,
            'QUAL': '.',
            'REF': 'AATATATT',
            'SAMPLES': {'H01': {'GT': '0/1'}}
        })[0]

        assert al.genome_reference == ref_genome
        assert al.chromosome == 'X'
        assert al.start_position == 41226488
        assert al.open_end_position == 41226495
        assert al.change_from == 'ATATATT'
        assert al.change_to == ''
        assert al.change_type == 'del'

    def test_indel(self, allele_importer, ref_genome):
        al = allele_importer.process({
            'ALT': ['AGCT'],
            'CHROM': 'X',
            'FILTER': '.',
            'ID': 'H186',
            'INFO': {},
            'POS': 41226488,
            'QUAL': '.',
            'REF': 'C',
            'SAMPLES': {'H01': {'GT': '0/1'}}
        })[0]

        assert al.genome_reference == ref_genome
        assert al.chromosome == 'X'
        assert al.start_position == 41226487
        assert al.open_end_position == 41226491
        assert al.change_from == 'C'
        assert al.change_to == 'AGCT'
        assert al.change_type == 'indel'
