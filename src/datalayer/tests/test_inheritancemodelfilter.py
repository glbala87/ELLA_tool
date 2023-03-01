"""
Integration/unit test for the AlleleFilter module.
Since it consists mostly of database queries, it's tested on a live database.
"""
from collections import defaultdict
from typing import List, Tuple

import hypothesis as ht
import hypothesis.strategies as st
import pytest

from conftest import mock_allele_with_annotation
from datalayer.allelefilter.inheritancemodelfilter import InheritanceModelFilter
from vardb.datamodel import annotationshadow, gene, genotype, sample

GLOBAL_CONFIG = {
    "frequencies": {
        "groups": {
            "external": {"ExAC": ["G", "FIN"], "1000g": ["G"], "esp6500": ["AA", "EA"]},
            "internal": {"inDB": ["AF"]},
        }
    },
    "transcripts": {"inclusion_regex": "NM_.*"},
}

GENES = ["GENE1", "GENE2", "GENE3"]
GENE_HGNC_ID = {k: int(1e6) * idx for idx, k in enumerate(GENES)}


def reset_genepanel(session, gene_inheritance: Tuple[List[str], List[str], List[str]]):
    """
    Creates
     - genepanel with 3 genes, each with inheritance from input
    """

    genepanel = gene.Genepanel(name="testpanel", version="v01", genome_reference="GRCh37")
    session.add(genepanel)
    session.flush()

    tx_idx = 0
    for idx, inheritances in enumerate(gene_inheritance):
        gene_name = f"GENE{idx+1}"
        g = gene.Gene(hgnc_id=GENE_HGNC_ID[gene_name], hgnc_symbol=gene_name)
        for inh in inheritances:
            tx_idx += 1
            t = gene.Transcript(
                gene=g,
                transcript_name=f"NM_{tx_idx}",
                type="RefSeq",
                genome_reference="",
                source="test",
                chromosome="1",
                tx_start=1000,
                tx_end=1500,
                strand="+",
                cds_start=1230,
                cds_end=1430,
                exon_starts=[1100, 1200, 1300, 1400],
                exon_ends=[1160, 1260, 1360, 1460],
            )
            session.add(t)
            session.flush()
            session.execute(
                gene.genepanel_transcript.insert(),
                {
                    "transcript_id": t.id,
                    "genepanel_name": genepanel.name,
                    "genepanel_version": genepanel.version,
                    "inheritance": inh,
                },
            )
    session.flush()


@st.composite
def inheritance_model_data(draw):
    gene_inheritance = []
    for _ in range(3):
        inheritance_strategy = st.sampled_from(["AD", "AR", "AD/AR", "XR", "XD", ""])
        gene_inheritance.append(draw(st.lists(inheritance_strategy, min_size=1, max_size=2)))

    num_alleles: int = draw(st.integers(min_value=1, max_value=5))
    alleles = list()
    for idx in range(num_alleles):
        gene = draw(st.lists(st.sampled_from(GENES), min_size=1, max_size=2, unique=True))
        # Draw random genotype (or None) per sample
        gt = draw(
            st.lists(st.sampled_from(["Homozygous", "Heterozygous", None]), min_size=3, max_size=3)
        )
        ht.assume(any(gt))  # We need at least one sample to have a genotype

        alleles.append((gene, gt))

    return (tuple(gene_inheritance), alleles)


def reset_analyses(session):
    session.execute("DELETE FROM interpretationlog")
    session.execute("DELETE FROM analysisinterpretation")
    session.execute("DELETE FROM genotypesampledata")
    session.execute("DELETE FROM genotype")
    session.execute("DELETE FROM sample")
    session.execute("DELETE FROM analysis")

    test_analysis = sample.Analysis(
        name="Test analysis", genepanel_name="testpanel", genepanel_version="v01"
    )
    session.add(test_analysis)
    session.flush()
    test_sample = sample.Sample(
        identifier="Test sample",
        analysis_id=test_analysis.id,
        proband=True,
        affected=True,
        sample_type="HTS",
    )
    test_sample2 = sample.Sample(
        identifier="Test sample 2",
        analysis_id=test_analysis.id,
        proband=True,
        affected=True,
        sample_type="HTS",
    )
    test_sample3 = sample.Sample(
        identifier="Test sample 3",
        analysis_id=test_analysis.id,
        proband=True,
        affected=True,
        sample_type="HTS",
    )
    session.add(test_sample)
    session.add(test_sample2)
    session.add(test_sample3)
    session.flush()
    return test_analysis, test_sample, test_sample2, test_sample3


def setup_fixtures(session, data):
    """
    Creates test genepanel, dummy analysis and alleles with annotation
    according to structure provided in data.

    Data example:
    (
        (["AR"], [""], [""]),  # Inheritance for GENE1, GENE2, GENE3
        [(["GENE1"], "Heterozygous")]  # List of alleles with gene and genotype
    )
    """
    gene_inheritance = data[0]
    allele_genes_genotypes = data[1]

    reset_genepanel(session, gene_inheritance)
    test_analysis, test_sample, test_sample2, test_sample3 = reset_analyses(session)

    allele_ids = []
    idx = 0
    for allele_genes, allele_gts in allele_genes_genotypes:
        # Insert allele located in genes according to input
        transcripts = list()
        for allele_gene in allele_genes:
            transcripts.append(
                {
                    "hgnc_id": GENE_HGNC_ID[allele_gene],
                    "symbol": allele_gene,
                    "transcript": "NM_DUMMY",
                }
            )
        al, _ = mock_allele_with_annotation(session, annotations={"transcripts": transcripts})
        session.flush()
        gt = genotype.Genotype(allele_id=al.id, sample_id=test_sample.id)

        sample_ids = [test_sample.id, test_sample2.id, test_sample3.id]
        for idx, allele_gt in enumerate(allele_gts):
            if allele_gt is None:
                continue
            gsd = genotype.GenotypeSampleData(
                genotype=gt,
                secondallele=False,
                multiallelic=False,
                sample_id=sample_ids[idx],
                type=allele_gt,
            )
            session.add(gsd)
        allele_ids.append(al.id)
        idx += 1

    session.flush()
    return test_analysis.id, allele_ids


class TestInheritanceModelFilter(object):
    @pytest.mark.aa(order=0)
    def test_prepare_data(self, test_database, session):
        test_database.refresh()  # Reset db

        # We need to recreate the annotation shadow tables,
        # since we want to use our test config
        # Delete existing filterconfigs and usergroups to avoid errors
        # when creating new shadow tables
        session.execute("DELETE FROM usergroupfilterconfig")
        session.execute("DELETE FROM filterconfig")
        session.execute("UPDATE usergroup SET config='{}'")
        annotationshadow.create_shadow_tables(session, GLOBAL_CONFIG)
        session.commit()

    # First index: Fixed tuple of inheritances (list) for GENE1, GENE2, GENE3
    # Second index: List of alleles with gene and genotype
    @ht.example(
        ((["AR"], [""], [""]), [(["GENE1"], ["Heterozygous", None, None])]), [0]
    )  # Single AR variant
    @ht.example(
        ((["XR"], [""], [""]), [(["GENE1"], ["Heterozygous", None, None])]), []
    )  # Single XR variant
    @ht.example(
        ((["AD"], [""], [""]), [(["GENE1"], ["Heterozygous", None, None])]), []
    )  # Single AD variant
    @ht.example(
        ((["AR/AD"], [""], [""]), [(["GENE1"], ["Heterozygous", None, None])]), []
    )  # Single mixed variant
    @ht.example(
        ((["AR"], [""], [""]), [(["GENE1"], ["Homozygous", None, None])]), []
    )  # Single AR hom variant
    @ht.example(
        ((["AD"], [""], [""]), [(["GENE1"], ["Homozygous", None, None])]), []
    )  # Single AR hom variant
    @ht.example(
        ((["AR/AD"], [""], [""]), [(["GENE1"], ["Homozygous", None, None])]), []
    )  # Single AR hom variant
    @ht.example(
        ((["AD"], ["AR"], [""]), [(["GENE1", "GENE2"], ["Heterozygous", None, None])]), []
    )  # Different inheritance in different genes
    @ht.example(
        ((["AR"], ["AD"], ["AR"]), [(["GENE2", "GENE3"], ["Heterozygous", None, None])]), []
    )
    @ht.example(
        (
            (["XR"], ["AR", "AR"], ["XR", "AD"]),
            [
                (["GENE1", "GENE3"], ["Heterozygous", None, None]),
                (["GENE1", "GENE3"], ["Heterozygous", None, None]),
                (["GENE2"], ["Heterozygous", None, None]),
            ],
        ),
        [2],
    )
    @ht.example(
        ((["AR"], [""], [""]), [(["GENE1"], ["Heterozygous", "Heterozygous", None])]), [0]
    )  # Multiple samples with same variant, all heterozygous
    @ht.example(
        ((["AR"], [""], [""]), [(["GENE1"], ["Homozygous", "Heterozygous", None])]), []
    )  # Multiple samples with same variant, conflicting genotype, one homozygous
    @ht.given(inheritance_model_data(), st.just(None))
    def test_recessive_non_candidates(self, session, data, manually_curated_result):
        session.rollback()

        analysis_id, allele_ids = setup_fixtures(session, data)

        imf = InheritanceModelFilter(session, GLOBAL_CONFIG)
        filter_config = {"filter_mode": "recessive_non_candidates"}
        result = imf.filter_alleles({analysis_id: allele_ids}, filter_config)

        if manually_curated_result is not None:
            curated_allele_ids = [allele_ids[idx] for idx in manually_curated_result]
            assert result[analysis_id] == set(curated_allele_ids)

        gene_inheritance, alleles = data

        # Criterias:
        # - single, heterozygous variant
        # - distinct AR and XR inheritance
        # across all genes for each allele
        is_gene_recessive = dict()
        for gene_name, inheritances in zip(GENES, gene_inheritance):
            is_gene_recessive[gene_name] = all(i == "AR" for i in inheritances)

        allele_id_heterozygous = dict()
        gene_allele_ids = defaultdict(set)

        for allele_id, allele_data in zip(allele_ids, alleles):
            gene_names, allele_gts = allele_data
            for gene_name in gene_names:
                gene_allele_ids[gene_name].add(allele_id)
            allele_id_heterozygous[allele_id] = all(
                gt in ["Heterozygous", None] for gt in allele_gts
            )

        filter_candidate_allele_id_gene = defaultdict(dict)  # {1: {"GENE1": False, "GENE2": True}}
        for gene_name in GENES:
            # Check whether gene has any alleles at all, if not continue
            if gene_name not in gene_allele_ids:
                continue
            allele_ids = list(gene_allele_ids[gene_name])
            for allele_id in allele_ids:
                if (
                    is_gene_recessive[gene_name]
                    and len(allele_ids) == 1
                    and allele_id_heterozygous[allele_id]
                ):
                    filter_candidate_allele_id_gene[allele_id][gene_name] = True
                else:
                    filter_candidate_allele_id_gene[allele_id][gene_name] = False

        result_allele_ids = set()
        for allele_id, per_gene_results in filter_candidate_allele_id_gene.items():
            if all(per_gene_results.values()):
                result_allele_ids.add(allele_id)

        assert result[analysis_id] == result_allele_ids, filter_candidate_allele_id_gene

    @ht.example(((["AD"], [""], [""]), [(["GENE1"], ["Homozygous", None, None])]), [])  # Is AD
    @ht.example(
        (
            (["AD"], [""], [""]),
            [(["GENE1"], ["Homozygous", None, None]), (["GENE1"], ["Heterozygous", None, None])],
        ),
        [],  # Multiple variants, but AD
    )
    @ht.example(
        ((["AD/AR"], [""], [""]), [(["GENE1"], ["Homozygous", None, None])]), [0]
    )  # Simple non-AD case
    @ht.example(
        (
            (["AD/AR"], [""], [""]),
            [(["GENE1"], ["Homozygous", None, None]), (["GENE1"], ["Heterozygous", None, None])],
        ),
        [0, 1],  # Multiple variants, same gene
    )
    @ht.example(
        (
            (["AD/AR"], [""], [""]),
            [(["GENE1"], ["Homozygous", None, None]), (["GENE2"], ["Heterozygous", None, None])],
        ),
        [0],
    )  # Multple variants, different genes
    @ht.example(
        ((["AD/AR"], [""], [""]), [(["GENE1"], ["Heterozygous", None, None])]), []
    )  # Single, but heterozygous
    @ht.example(
        (
            (["AD"], ["AD"], [""]),
            [(["GENE1"], ["Homozygous", None, None]), (["GENE2"], ["Homozygous", None, None])],
        ),
        [],
    )
    @ht.example(
        ((["AR"], [""], [""]), [(["GENE1"], ["Heterozygous", "Heterozygous", None])]), []
    )  # Multiple samples with same variant, all heterozygous
    @ht.example(
        ((["AR"], [""], [""]), [(["GENE1"], ["Homozygous", "Heterozygous", None])]), [0]
    )  # Multiple samples with same variant, conflicting genotype, one homozygous
    @ht.given(inheritance_model_data(), st.just(None))
    def test_recessive_candidates(self, session, data, manually_curated_result):
        session.rollback()

        analysis_id, allele_ids = setup_fixtures(session, data)

        imf = InheritanceModelFilter(session, GLOBAL_CONFIG)
        filter_config = {"filter_mode": "recessive_candidates"}
        result = imf.filter_alleles({analysis_id: allele_ids}, filter_config)

        if manually_curated_result is not None:
            curated_allele_ids = [allele_ids[idx] for idx in manually_curated_result]
            assert result[analysis_id] == set(curated_allele_ids)

        gene_inheritance, alleles = data

        # Criterias:
        # - single homozygous variant or multiple variants
        # - not distinct AD inheritance

        gene_distinct_ad = dict()
        for gene_name, inheritances in zip(GENES, gene_inheritance):
            gene_distinct_ad[gene_name] = all(i == "AD" for i in inheritances)

        allele_id_homozygous = dict()
        gene_allele_ids = defaultdict(set)

        for allele_id, allele_data in zip(allele_ids, alleles):
            gene_names, allele_gts = allele_data
            for gene_name in gene_names:
                gene_allele_ids[gene_name].add(allele_id)
            allele_id_homozygous[allele_id] = any(gt == "Homozygous" for gt in allele_gts)

        filter_candidate_allele_id_gene = defaultdict(dict)  # {1: {"GENE1": False, "GENE2": True}}
        for gene_name in GENES:
            # Check whether gene has any alleles at all, if not continue
            if gene_name not in gene_allele_ids:
                continue
            allele_ids = list(gene_allele_ids[gene_name])
            for allele_id in allele_ids:
                if not gene_distinct_ad[gene_name] and (
                    (len(allele_ids) == 1 and allele_id_homozygous[allele_id])
                    or (len(allele_ids) > 1)
                ):
                    filter_candidate_allele_id_gene[allele_id][gene_name] = True
                else:
                    filter_candidate_allele_id_gene[allele_id][gene_name] = False

        result_allele_ids = set()
        for allele_id, per_gene_results in filter_candidate_allele_id_gene.items():
            if any(per_gene_results.values()):
                result_allele_ids.add(allele_id)

        assert result[analysis_id] == result_allele_ids, filter_candidate_allele_id_gene
