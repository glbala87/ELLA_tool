"""
The test-sample is of this form:

#CHROM	POS	ID	REF	ALT	QUAL	FILTER	INFO	FORMAT	TrioMK	TrioPK	TrioFK
13	32914458	.	C	G	5000	PASS	.	GT	0|1	0|0	0|0
13	32914484	.	C	T	5000	PASS	.	GT	1|1	0|0	0|0
13	32914522	.	C	A	5000	PASS	.	GT	1|0	1|0	0|0
13	32914550	.	GAACA	G	5000	PASS	.	GT	1|0	1|0	1|0
13	32914569	.	C	CA	5000	PASS	.	GT	0|1	1|0	0|0
13	32914616	.	C	T	5000	PASS	.	GT	0|1	1|0	0|1
13	32914617	.	A	C,G	5000	PASS	.	GT	1|2	1|0	0|2
13	32914688	.	GTT	ATT,GT,G	5000	PASS	.	GT	1|3	1|0	2|3
13	32914766	.	CTTCACTA	GTTCACTA,C	5000	PASS	.	GT	0|0	1|0	0|2

This should import as:
- 1 analysis
- 3 samples
- 20 genotypes
    - 8 for TrioMK
    - 7 for TrioPK
    - 5 for TrioFK
- 13 alleles
- Other tests
    - One homozygous genotype (13,32914484,C->T)
    - Three multiallelic heterozygous genotypes
    - One genotype in all three samples (13, 32914550, GAACA->G)
"""

import pytest
import os
from vardb.deposit.deposit_analysis import DepositAnalysis
from vardb.datamodel import genotype, sample
from vardb.datamodel.analysis_config import AnalysisConfigData

import vardb
VARDB_PATH = os.path.split(vardb.__file__)[0]


## FIXTURES

@pytest.fixture(scope="module", autouse=True)
def deposit(session):
    """Deposit test analysis"""
    trio = os.path.join(VARDB_PATH, "testdata/analyses/trio/trio_analysis_1.HBOC_v01")
    assert os.path.isdir(trio)
    files = os.listdir(trio)
    assert len(files) == 1+1+3
    vcf_file = os.path.join(trio, [f for f in files if f.endswith(".vcf")][0])

    deposit_analysis = DepositAnalysis(session)
    deposit_analysis.import_vcf(AnalysisConfigData(
        vcf_file,
        'trio_analysis_1.HBOC_v01',
        'HBOC',
        'v01',
        1
    ))


@pytest.fixture(scope="module")
def analysis_name():
    return "trio_analysis_1.HBOC_v01"


@pytest.fixture(scope="module")
def all_genotypes(session, analysis_name):
    """return all genotypes imported in this analysis"""
    all_genotypes = session.query(genotype.Genotype).join(
        sample.Analysis
    ).filter(
        sample.Analysis.name == analysis_name,
    ).all()
    return all_genotypes


## TESTS

def test_analysis(session, analysis_name):
    """Test that there is only one analysis with given name"""
    analyses = session.query(sample.Analysis).filter(
        sample.Analysis.name == analysis_name,
    ).all()
    assert len(analyses) == 1


def test_num_samples_in_analysis(session, analysis_name):
    """Test number of samples in analysis"""
    samples = session.query(sample.Sample).join(
        sample.Analysis,
    ).filter(
        sample.Analysis.name == analysis_name,
    ).all()
    assert len(samples) == 3
    assert set(s.identifier for s in samples) == set(["TrioMK", "TrioPK", "TrioFK"])


def test_num_genotypes(all_genotypes):
    """Test number of genotypes in analysis"""
    assert len(all_genotypes) == 20


def test_number_of_alleles(all_genotypes):
    """Test number of alleles"""
    allele_ids = set(sum(([gt.allele_id, gt.secondallele_id] for gt in all_genotypes), []))
    allele_ids.discard(None)
    assert len(allele_ids) == 13


@pytest.mark.parametrize(("sample_name", "expected"), [
    ("TrioMK", 8),
    ("TrioFK", 5),
    ("TrioPK", 7)
])
def test_number_of_genotypes_in_sample(all_genotypes, sample_name, expected):
    """Test number of genotypes for each sample"""
    genotypes_in_sample = [gt for gt in all_genotypes if gt.sample.identifier == sample_name]
    assert len(genotypes_in_sample) == expected


def test_homozygous(all_genotypes):
    """One homozygous genotype (13,32914484,C->T)"""
    homozygous = [gt for gt in all_genotypes if gt.homozygous]
    assert len(homozygous) == 1
    homozygous = homozygous[0]
    assert homozygous.secondallele is None
    allele = homozygous.allele
    assert allele.chromosome == '13'
    assert allele.vcf_pos == 32914484
    assert allele.vcf_ref == 'C'
    assert allele.vcf_alt == 'T'


def test_multiallelic_heterozygous(all_genotypes):
    """Three multiallelic heterozygous genotypes"""
    heterozygous_nonref = [gt for gt in all_genotypes if gt.secondallele]
    assert len(heterozygous_nonref) == 3


def test_common_genotype(all_genotypes):
    """One genotype in all three samples (13, 32914550, GAACA->G)"""
    genotypes = [gt for gt in all_genotypes
                 if (gt.allele.chromosome == '13' and
                     gt.allele.vcf_pos == 32914550 and
                     gt.allele.vcf_ref == "GAACA" and
                     gt.allele.vcf_alt == 'G' and
                     gt.secondallele is None)
                 ]
    assert len(genotypes) == 3
    gt_samples = [gt.sample.identifier for gt in genotypes]
    assert set(gt_samples) == set(["TrioMK", "TrioPK", "TrioFK"])
