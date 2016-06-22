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
def annotation_importer(session):
    return deposit.AnnotationImporter(session)


@pytest.fixture
def allele_importer(session, ref_genome):
    return deposit.AlleleImporter(session, ref_genome=ref_genome)


class TestGenotypeImporter():

    def test_genotype(self, genotype_importer):

        db_alleles = [allele.Allele(), allele.Allele()]
        db_sample = sample.Sample()
        db_analysis = sample.Analysis()
        samples = {
            'TEST_1': {
                'GT': '0/1'
            },
            'TEST_2': {
                'GT': '1|1',
                'GQ': 234.4,
                'DP': 12
            },
            'TEST_3': {
                'GT': '2/1',
                'GQ': 234.4,
                'DP': 12
            }
        }

        data1 = {
            'QUAL': '.',
            'ID': 'H186',
            'POS': 1234,
            'REF': 'T',
            'ALT': ['A', 'G'],
            'FILTER': 'PASS',
            'SAMPLES': samples
        }

        result1 = genotype_importer.process(data1, 'TEST_1', db_analysis, db_sample, db_alleles)

        assert result1.allele == db_alleles[0]
        # Second allele will only be set if heterozygous non-ref
        assert result1.secondallele is None
        assert result1.homozygous is False
        assert result1.sample == db_sample
        assert result1.genotypeQuality is None
        assert result1.sequencingDepth is None
        assert result1.variantQuality is None

        data2 = {
            'QUAL': 456,
            'ID': 'H186',
            'POS': 1234,
            'REF': 'T',
            'ALT': ['A', 'G'],
            'FILTER': 'PASS',
            'SAMPLES': samples
        }

        result2 = genotype_importer.process(data2, 'TEST_2', db_analysis, db_sample, db_alleles)

        assert result2.allele == db_alleles[0]
        assert result2.secondallele is None
        assert result2.homozygous is True
        assert result2.sample == db_sample
        assert result2.genotypeQuality == 234.4
        assert result2.sequencingDepth == 12
        assert result2.variantQuality == 456

        data3 = {
            'QUAL': 456,
            'ID': 'H186',
            'POS': 1234,
            'REF': 'T',
            'ALT': ['A', 'G'],
            'FILTER': 'PASS',
            'SAMPLES': samples
        }

        result3 = genotype_importer.process(data3, 'TEST_3', db_analysis, db_sample, db_alleles)

        assert result3.allele == db_alleles[1]
        assert result3.secondallele == db_alleles[0]
        assert result3.homozygous is False
        assert result3.sample == db_sample
        assert result3.genotypeQuality == 234.4
        assert result3.sequencingDepth == 12
        assert result3.variantQuality == 456


class TestAnnotationImporter():

    def test_annotation(self, annotation_importer):

        alleles = [mock.Mock(), mock.Mock()]
        ai1, ai2 = annotation_importer.process({
            'ID': 'H186',
            'ALT': ['A', 'G'],
            'INFO': {
                'A': {
                    'EFF': 'TestA'
                },
                'G': {
                    'EFF': 'TestG'
                },
                'ALL': {
                    'Common': 'SomeData'
                }
            }

        }, alleles)

        assert ai1.annotations == {
            'id': 'H186',
            'Common': 'SomeData',
            'EFF': 'TestA'
        }

        assert ai2.annotations == {
            'id': 'H186',
            'Common': 'SomeData',
            'EFF': 'TestG'
        }


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

        assert allele.genomeReference == ref_genome
        assert allele.chromosome == '17'
        assert allele.startPosition == 41226487
        assert allele.openEndPosition == 41226488
        assert allele.changeFrom == 'C'
        assert allele.changeTo == 'A'
        assert allele.changeType == 'SNP'

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

        assert al1.genomeReference == ref_genome
        assert al1.chromosome == '17'
        assert al1.startPosition == 41226487
        assert al1.openEndPosition == 41226488
        assert al1.changeFrom == 'C'
        assert al1.changeTo == 'A'
        assert al1.changeType == 'SNP'

        assert al2.genomeReference == ref_genome
        assert al2.chromosome == '17'
        assert al2.startPosition == 41226487
        assert al2.openEndPosition == 41226488
        assert al2.changeFrom == 'C'
        assert al2.changeTo == 'G'
        assert al2.changeType == 'SNP'

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

        assert al.genomeReference == ref_genome
        assert al.chromosome == 'X'
        assert al.startPosition == 41226488
        assert al.openEndPosition == 41226491
        assert al.changeFrom == ''
        assert al.changeTo == 'GCT'
        assert al.changeType == 'ins'

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

        assert al.genomeReference == ref_genome
        assert al.chromosome == 'X'
        assert al.startPosition == 41226488
        assert al.openEndPosition == 41226495
        assert al.changeFrom == 'ATATATT'
        assert al.changeTo == ''
        assert al.changeType == 'del'

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

        assert al.genomeReference == ref_genome
        assert al.chromosome == 'X'
        assert al.startPosition == 41226487
        assert al.openEndPosition == 41226491
        assert al.changeFrom == 'C'
        assert al.changeTo == 'AGCT'
        assert al.changeType == 'indel'
