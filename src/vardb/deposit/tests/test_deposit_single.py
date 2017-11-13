import pytest
import os
from vardb.deposit.deposit_analysis import DepositAnalysis
from vardb.datamodel import genotype, sample

import vardb
VARDB_PATH = os.path.split(vardb.__file__)[0]

## HELPER FUNCTIONS


def get_genotype(genotypes, first_change, second_change, _ret=[]):
    gts = []
    for gt in genotypes:
        if second_change is not None and gt.secondallele is None:
            continue
        elif second_change is None and gt.secondallele is None:
            if gt.allele.change_type == first_change:
                gts.append(gt)
        elif set([gt.allele.change_type, gt.secondallele.change_type]) == set([first_change, second_change]):
            gts.append(gt)
    return gts



## FIXTURES

@pytest.fixture(scope="module")
def all_genotypes_single(session):
    """return all genotypes imported in this analysis"""
    analysis_name = "brca_decomposed.HBOC_v01"
    all_genotypes = session.query(genotype.Genotype).join(
        sample.Analysis
    ).filter(
        sample.Analysis.name == analysis_name,
    ).all()
    return all_genotypes


## TESTS

# There should be one heterozygous SNP, del, and ins (singleallelic)
@pytest.mark.parametrize("variant_type", ("SNP", "ins", "del"))
def test_single_singlealleic(all_genotypes_single, variant_type):
    gts = get_genotype(all_genotypes_single, variant_type, None)
    assert len(gts) == 1
    gt = gts[0]
    assert gt.secondallele is None
    assert "REF" in gt.allele_depth
    assert len(gt.allele_depth) == 2
    assert gt.allele.vcf_alt in gt.allele_depth


@pytest.mark.parametrize("variant_types", (
        ("SNP", "SNP"),
        ("SNP", "ins"),
        ("SNP", "del"),
        ("ins", "del")
    ))
def test_single_multiallelic(all_genotypes_single, variant_types):
    # There should be one heterozygous SNP,SNP (multiallelic)
    gts = get_genotype(all_genotypes_single, *variant_types)
    assert len(gts) == 1
    gt = gts[0]
    assert gt.allele.id != gt.secondallele.id
    assert gt.allele.vcf_pos == gt.secondallele.vcf_pos
    assert "REF" in gt.allele_depth
    assert len(gt.allele_depth) == 3
    assert gt.allele.vcf_alt in gt.allele_depth
    assert gt.secondallele.vcf_alt in gt.allele_depth
