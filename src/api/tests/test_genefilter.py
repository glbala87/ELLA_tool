"""
Integration/unit test for the AlleleFilter module.
Since it consists mostly of database queries, it's tested on a live database.
"""

from api.allelefilter.genefilter import GeneFilter
from vardb.datamodel import allele, annotation, gene

import hypothesis as ht
import hypothesis.strategies as st


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


def create_genepanel(hgnc_ids_transcripts):
    # Create fake genepanel for testing purposes

    genepanel = gene.Genepanel(name="testpanel", version="v01", genome_reference="GRCh37")

    genepanel.transcripts = []
    genepanel.phenotypes = []

    for hgnc_id, transcript_name in hgnc_ids_transcripts:
        g = gene.Gene(hgnc_id=hgnc_id, hgnc_symbol="GENE{}".format(hgnc_id))

        tx = gene.Transcript(
            gene=g,
            transcript_name=transcript_name,
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

        genepanel.transcripts.append(tx)

    return genepanel


def get_hgnc_id():
    return st.integers(min_value=1e6, max_value=1e6 + 20)


@st.composite
def genepanel(draw):
    hgnc_id = draw(get_hgnc_id())
    transcript = "NM_{}.1".format(hgnc_id)
    return (hgnc_id, transcript)


@st.composite
def annotations(draw):
    # Some alleles could be without annotations
    N = draw(st.integers(min_value=0, max_value=4))
    ann = {"transcripts": []}
    for i in range(N):
        hgnc_id = draw(get_hgnc_id())
        transcript = "NM_{}.1".format(hgnc_id)
        ann["transcripts"].append({"hgnc_id": hgnc_id, "transcript": transcript})
    return ann


@st.composite
def filter_config(draw):
    return {
        "mode": draw(st.sampled_from(["one", "all"])),
        "inverse": draw(st.booleans()),
        "genes": draw(st.lists(get_hgnc_id(), unique=True, min_size=1)),
    }


@ht.given(
    st.lists(genepanel(), min_size=1, unique=True),
    st.lists(annotations(), min_size=5),
    st.one_of(filter_config()),
)
def test_gene_filter(session, genepanel, annotations, fc):
    session.rollback()
    gp = create_genepanel(genepanel)
    session.add(gp)
    gp_tx = [tx.transcript_name for tx in gp.transcripts]

    allele_ids = []
    allele_id_genes = {}
    for ann in annotations:
        al, an = create_allele_with_annotation(session, ann)

        session.flush()
        allele_ids.append(al.id)
        allele_id_genes[al.id] = [
            tx["hgnc_id"] for tx in ann["transcripts"] if tx["transcript"] in gp_tx
        ]

    gf = GeneFilter(session, None)
    result = gf.filter_alleles({(gp.name, gp.version): allele_ids}, fc)[gp.name, gp.version]

    if fc["mode"] == "one":
        expected_result = [
            allele_id
            for allele_id, genes in allele_id_genes.items()
            if set(genes) and set(genes) & set(fc["genes"])
        ]
    else:
        expected_result = [
            allele_id
            for allele_id, genes in allele_id_genes.items()
            if set(genes) and set(genes) - set(fc["genes"]) == set()
        ]

    if fc["inverse"]:
        expected_result = list(set(allele_ids) - set(expected_result))

    assert set(expected_result) == set(result)
