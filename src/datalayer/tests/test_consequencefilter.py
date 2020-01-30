"""
Integration/unit test for the AlleleFilter module.
Since it consists mostly of database queries, it's tested on a live database.
"""
import copy
import pytest

from datalayer.allelefilter.consequencefilter import ConsequenceFilter
from vardb.datamodel import allele, annotation, gene, annotationshadow, assessment

import hypothesis as ht
import hypothesis.strategies as st


# prevent screen getting filled with output (useful when testing manually)
# import logging
# logging.getLogger('vardb.deposit.deposit_genepanel').setLevel(logging.CRITICAL)


GLOBAL_CONFIG = {
    "frequencies": {
        "groups": {
            "external": {"ExAC": ["G", "FIN"], "1000g": ["G"], "esp6500": ["AA", "EA"]},
            "internal": {"inDB": ["AF"]},
        }
    },
    "transcripts": {
        "consequences": [
            "transcript_ablation",
            "splice_donor_variant",
            "splice_acceptor_variant",
            "stop_gained",
            "frameshift_variant",
            "start_lost",
            "initiator_codon_variant",
            "stop_lost",
            "inframe_insertion",
            "inframe_deletion",
            "missense_variant",
            "protein_altering_variant",
            "transcript_amplification",
            "splice_region_variant",
            "incomplete_terminal_codon_variant",
            "synonymous_variant",
            "stop_retained_variant",
            "coding_sequence_variant",
            "mature_miRNA_variant",
            "5_prime_UTR_variant",
            "3_prime_UTR_variant",
            "non_coding_transcript_exon_variant",
            "non_coding_transcript_variant",
            "intron_variant",
            "NMD_transcript_variant",
            "upstream_gene_variant",
            "downstream_gene_variant",
            "TFBS_ablation",
            "TFBS_amplification",
            "TF_binding_site_variant",
            "regulatory_region_variant",
            "regulatory_region_ablation",
            "regulatory_region_amplification",
            "feature_elongation",
            "feature_truncation",
            "intergenic_variant",
        ],
        "inclusion_regex": "NM_.*",
    },
}


@st.composite
def allele_positions(draw, chromosome, start, end):
    start_position = draw(st.integers(min_value=start, max_value=end))
    end_position = draw(st.integers(min_value=start_position + 1, max_value=start_position + 50))
    return (chromosome, start_position, end_position)


allele_start = 1300


def create_allele(data=None):
    global allele_start
    allele_start += 1
    default_allele_data = {
        "chromosome": "1",
        "start_position": allele_start,
        "open_end_position": allele_start + 1,
        "change_from": "A",
        "change_to": "T",
        "change_type": "SNP",
        "vcf_pos": allele_start + 1,
        "vcf_ref": "A",
        "vcf_alt": "T",
    }
    if data:
        for k in data:
            default_allele_data[k] = data[k]
    data = default_allele_data

    return allele.Allele(genome_reference="GRCh37", **data)


def create_annotation(annotations, allele=None):
    annotations.setdefault("external", {})
    annotations.setdefault("frequencies", {})
    annotations.setdefault("prediction", {})
    annotations.setdefault("references", [])
    annotations.setdefault("transcripts", [])
    for t in annotations["transcripts"]:
        t.setdefault("consequences", [])
        t.setdefault("transcript", "NONE_DEFINED")
        t.setdefault("strand", 1)
        t.setdefault("is_canonical", True)
        t.setdefault("in_last_exon", "no")
    return annotation.Annotation(annotations=annotations, allele=allele)


def create_allele_with_annotation(session, annotations=None, allele_data=None):
    al = create_allele(data=allele_data)
    session.add(al)
    if annotations is not None:
        an = create_annotation(annotations, allele=al)
        session.add(an)
    else:
        an = None

    return al, an


def create_genepanel():
    # Create fake genepanel for testing purposes

    g1 = gene.Gene(hgnc_id=int(1e6), hgnc_symbol="GENE1")

    t1 = gene.Transcript(
        gene=g1,
        transcript_name="NM_1",
        type="RefSeq",
        genome_reference="",
        chromosome="1",
        tx_start=1000,
        tx_end=1500,
        strand="+",
        cds_start=1230,
        cds_end=1430,
        exon_starts=[1100, 1200, 1300, 1400],
        exon_ends=[1160, 1260, 1360, 1460],
    )

    genepanel = gene.Genepanel(name="testpanel", version="v01", genome_reference="GRCh37")

    genepanel.transcripts = [t1]
    genepanel.phenotypes = []
    return genepanel


@st.composite
def filter_config(draw):
    consequences = draw(
        st.lists(elements=st.sampled_from(GLOBAL_CONFIG["transcripts"]["consequences"]), min_size=1)
    )
    genepanel_only = draw(st.booleans())
    return {"consequences": consequences, "genepanel_only": genepanel_only}


@st.composite
def transcripts(draw):
    N = draw(st.integers(min_value=1, max_value=10))
    tx = []
    for i in range(N):
        gene_symbol = draw(st.sampled_from(["GENE1", "SOME_RANDOM_GENE"]))
        transcript = draw(st.sampled_from(["NM_1.1", "NM_SOMETHING", "SOME_OTHER_TRANSCRIPT"]))
        consequences = draw(
            st.lists(
                elements=st.sampled_from(GLOBAL_CONFIG["transcripts"]["consequences"]), min_size=1
            )
        )
        tx.append({"symbol": gene_symbol, "transcript": transcript, "consequences": consequences})

    return tx


class TestConsequenceFilter(object):
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

        gp = create_genepanel()
        session.add(gp)
        session.commit()

    @ht.given(st.one_of(filter_config()), st.lists(transcripts(), min_size=1))
    def test_consequence_filter(self, session, filter_config, transcripts):
        session.rollback()
        genepanel_consequences = dict()
        all_consequences = dict()
        allele_ids = []
        for tx in transcripts:
            al, _ = create_allele_with_annotation(session, {"transcripts": tx})
            session.flush()
            allele_ids.append(al.id)
            include_tx = [t for t in tx if t["transcript"].startswith("NM_")]
            genepanel_consequences[al.id] = set(
                sum([t["consequences"] for t in include_tx if t["symbol"] == "GENE1"], [])
            )
            all_consequences[al.id] = set(sum([t["consequences"] for t in include_tx], []))

        gp_key = ("testpanel", "v01")
        cf = ConsequenceFilter(session, GLOBAL_CONFIG)
        result = cf.filter_alleles({gp_key: allele_ids}, filter_config)

        expected_result = set()
        check_consequences = (
            genepanel_consequences if filter_config["genepanel_only"] else all_consequences
        )
        for a_id in allele_ids:
            if set(filter_config["consequences"]) & check_consequences[a_id]:
                expected_result.add(a_id)

        assert result[gp_key] == expected_result
