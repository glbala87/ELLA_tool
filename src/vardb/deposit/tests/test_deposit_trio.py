

import pytest
import os
from vardb.util import vcfiterator
from vardb.deposit.deposit_analysis import DepositAnalysis
from vardb.deposit.importers import SampleImporter
from vardb.datamodel import genotype, sample, allele
from vardb.datamodel.analysis_config import AnalysisConfigData

import vardb

VARDB_PATH = os.path.split(vardb.__file__)[0]
TRIO_PATH = os.path.join(VARDB_PATH, "testdata/analyses/integration_testing/trio_variants_1.HBOC_v01")


## FIXTURES

@pytest.fixture(scope="module", autouse=True)
def deposit(test_database, session_module):
    """Deposit test analysis"""
    test_database.refresh()

    assert os.path.isdir(TRIO_PATH)
    files = os.listdir(TRIO_PATH)

    vcf_file = os.path.join(TRIO_PATH, [f for f in files if f.endswith(".vcf")][0])
    ped_file = os.path.join(TRIO_PATH, [f for f in files if f.endswith(".ped")][0])
    deposit_analysis = DepositAnalysis(session_module)
    deposit_analysis.import_vcf(
        AnalysisConfigData(
            vcf_file,
            'trio_variants_1.HBOC_v01',
            'HBOC',
            'v01',
            1
        ),
        ped_file=ped_file
    )
    session_module.commit()


@pytest.fixture(scope="module")
def ped_data():
    files = os.listdir(TRIO_PATH)
    return SampleImporter.parse_ped(
        os.path.join(TRIO_PATH, [f for f in files if f.endswith(".ped")][0])
    )


@pytest.fixture(scope="module")
def analysis_name():
    return "trio_variants_1.HBOC_v01"


@pytest.fixture(scope="module")
def all_genotypes(session_module, analysis_name):
    """return all genotypes imported in this analysis"""
    all_genotypes = session_module.query(genotype.Genotype).join(
        sample.Analysis
    ).filter(
        sample.Analysis.name == analysis_name,
    ).all()
    return all_genotypes


## TESTS

def test_pedigree(session_module, analysis_name, ped_data):
    """Test that there is only one analysis with given name"""
    samples = session_module.query(sample.Sample).join(
        sample.Analysis
    ).filter(
        sample.Analysis.name == analysis_name,
    ).all()

    proband = next(s for s in samples if s.identifier == 'TrioP')
    proband_ped = next(p for p in ped_data if p['sample_id'] == 'TrioP')
    father = next(s for s in samples if s.identifier == 'TrioF')
    father_ped = next(p for p in ped_data if p['sample_id'] == 'TrioF')
    mother = next(s for s in samples if s.identifier == 'TrioM')
    mother_ped = next(p for p in ped_data if p['sample_id'] == 'TrioM')

    assert proband.family_id == proband_ped['family_id']
    assert proband.sex == proband_ped['sex']
    assert proband.affected is proband_ped['affected']
    assert proband.father_id == father.id
    assert proband.mother_id == mother.id

    assert father.family_id == father_ped['family_id']
    assert father.sex == father_ped['sex']
    assert father.affected is father_ped['affected']
    assert father.father_id is None
    assert father.mother_id is None

    assert mother.family_id == mother_ped['family_id']
    assert mother.sex == mother_ped['sex']
    assert mother.affected is mother_ped['affected']
    assert mother.mother_id is None
    assert mother.mother_id is None


def test_data_import(session_module, analysis_name):
    files = os.listdir(TRIO_PATH)
    vcf_file = os.path.join(TRIO_PATH, [f for f in files if f.endswith(".vcf")][0])

    vi = vcfiterator.VcfIterator(vcf_file)

    analysis_id = session_module.query(sample.Analysis.id).filter(
        sample.Analysis.name == analysis_name
    ).scalar()

    sample_id_names = session_module.query(
        sample.Sample.id,
        sample.Sample.identifier
    ).filter(
        sample.Sample.analysis_id == analysis_id
    ).all()

    sample_id_names = {s[0]: s[1] for s in sample_id_names}

    def check_allele_variant(allele, variant):
        assert allele.chromosome == variant['CHROM']
        assert allele.vcf_pos == variant['POS']
        assert allele.vcf_ref == variant['REF']
        assert len(variant['ALT']) == 1
        assert allele.vcf_alt == variant['ALT'][0]

    for variant in vi.iter():

        genotypes = session_module.query(genotype.Genotype).join(
            allele.Allele.genotypes
        ).filter(
            allele.Allele.chromosome == variant['CHROM'],
            allele.Allele.vcf_pos == variant['POS'],
            allele.Allele.vcf_ref == variant['REF'],
            allele.Allele.vcf_alt == variant['ALT'][0],
            genotype.Genotype.analysis_id == analysis_id
        ).all()

        assert genotypes

        for gt in genotypes:
            vcf_genotype = variant['SAMPLES'][sample_id_names[gt.sample_id]]['GT']
            gts = vcf_genotype.split('/', 1)
            if gts == ['1', '1']:
                check_allele_variant(gt.allele, variant)
                assert gt.homozygous is True
            elif gts in [['0', '1'], ['1', '0']]:
                check_allele_variant(gt.allele, variant)
                assert gt.homozygous is False
            elif gts == ['1', '.']:
                check_allele_variant(gt.allele, variant)
                assert gt.homozygous is False
            elif gts == ['.', '1']:
                assert gt.homozygous is False
                check_allele_variant(gt.secondallele, variant)
            else:
                raise RuntimeError("Case {} not covered".format(gts))


def test_analysis(session_module, analysis_name):
    analyses = session_module.query(sample.Analysis).filter(
        sample.Analysis.name == analysis_name,
    ).all()
    assert len(analyses) == 1


def test_samples_in_analysis(session_module, analysis_name):
    samples = session_module.query(sample.Sample).join(
        sample.Analysis,
    ).filter(
        sample.Analysis.name == analysis_name,
    ).all()
    assert len(samples) == 3
    assert set(s.identifier for s in samples) == set(["TrioM", "TrioP", "TrioF"])
    proband = next(s for s in samples if s.identifier == 'TrioP')
    father = next(s for s in samples if s.identifier == 'TrioF')
    mother = next(s for s in samples if s.identifier == 'TrioM')

    assert proband.proband is True
    assert proband.affected is True
    assert proband.father_id == father.id
    assert proband.mother_id == mother.id

    assert father.proband is False
    assert father.affected is False
    assert father.father_id is None
    assert father.mother_id is None

    assert mother.proband is False
    assert mother.affected is False
    assert mother.father_id is None
    assert mother.mother_id is None
