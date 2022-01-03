from sqlalchemy import tuple_
from datalayer import queries
from vardb.datamodel import gene
from conftest import mock_allele_with_annotation


def test_distinct_inheritance_hgnc_ids_for_genepanel(session):

    testpanels = [("HBOCUTV", "v01"), ("OMIM", "v01")]

    for panel in testpanels:
        ad_hgnc_ids = queries.distinct_inheritance_hgnc_ids_for_genepanel(
            session, "AD", panel[0], panel[1]
        ).all()
        ad_hgnc_ids = [a[0] for a in ad_hgnc_ids]

        # Make sure all genes are actually part of input genepanel
        assert (
            session.query(gene.Transcript.gene_id)
            .join(gene.Genepanel.transcripts)
            .join(gene.Gene)
            .filter(
                tuple_(gene.Genepanel.name, gene.Genepanel.version) == panel,
                gene.Gene.hgnc_symbol.in_(ad_hgnc_ids),
            )
            .distinct()
            .count()
            == len(ad_hgnc_ids)
        )

        # Test that AD matches only has 'AD' phenotypes
        inheritances = (
            session.query(gene.Phenotype.inheritance)
            .join(gene.Gene)
            .join(gene.genepanel_phenotype)
            .filter(
                tuple_(
                    gene.genepanel_phenotype.c.genepanel_name,
                    gene.genepanel_phenotype.c.genepanel_version,
                )
                == panel,
                gene.Gene.hgnc_id.in_(ad_hgnc_ids),
            )
            .all()
        )
        assert all(i[0] == "AD" for i in inheritances)

        # Test opposite case: non-AD genes has at least one non-AD phenotype
        inheritances = (
            session.query(gene.Phenotype.gene_id, gene.Phenotype.inheritance)
            .join(gene.Gene)
            .join(gene.genepanel_phenotype)
            .filter(
                tuple_(
                    gene.genepanel_phenotype.c.genepanel_name,
                    gene.genepanel_phenotype.c.genepanel_version,
                )
                == panel,
                ~gene.Gene.hgnc_id.in_(ad_hgnc_ids),
            )
            .all()
        )

        gene_ids = set([i[0] for i in inheritances])
        for gene_id in gene_ids:
            gene_inheritances = [i[1] for i in inheritances if i[0] == gene_id]
            assert any(i != "AD" for i in gene_inheritances)


def test_annotation_transcripts_genepanel(session, test_database):

    test_database.refresh()

    def insert_data():

        g1 = gene.Gene(hgnc_id=1, hgnc_symbol="GENE1")
        g2 = gene.Gene(hgnc_id=2, hgnc_symbol="GENE2")
        g3 = gene.Gene(hgnc_id=3, hgnc_symbol="GENE3")
        transcript_base = {
            "type": "RefSeq",
            "genome_reference": "123",
            "chromosome": "123",
            "tx_start": 123,
            "tx_end": 123,
            "strand": "+",
            "cds_start": 123,
            "cds_end": 123,
            "exon_starts": [123, 321],
            "exon_ends": [123, 321],
        }

        t1 = gene.Transcript(gene=g1, name="NM_1.1", **transcript_base)

        t21 = gene.Transcript(gene=g2, name="NM_2.1", **transcript_base)

        t22 = gene.Transcript(gene=g2, name="NM_2.2", **transcript_base)

        t3 = gene.Transcript(gene=g3, name="NM_3.1", **transcript_base)

        genepanel1 = gene.Genepanel(name="testpanel1", version="v01", genome_reference="GRCh37")
        genepanel1.transcripts = [t1, t21]
        genepanel1.phenotypes = []
        session.add(genepanel1)

        genepanel2 = gene.Genepanel(name="testpanel2", version="v01", genome_reference="GRCh37")

        genepanel2.transcripts = [t22, t3]
        genepanel1.phenotypes = []
        session.add(genepanel2)

        a1, _ = mock_allele_with_annotation(
            session,
            annotations={
                "transcripts": [
                    {"transcript": "NM_1.1", "hgnc_id": 1},  # In genepanel
                    {"transcript": "NM_1", "hgnc_id": 1},  # In genepanel, no version
                    {
                        "transcript": "NM_2.2",
                        "hgnc_id": 2,
                    },  # In two genepanels, different version in one
                    {"transcript": "NM_NOT_IN_PANEL.1", "hgnc_id": 1},  # Not in genepanel
                    {"transcript": "NM_NOT_IN_PANEL", "hgnc_id": 2},  # Not in genepanel, no version
                ]
            },
        )

        a2, _ = mock_allele_with_annotation(
            session,
            annotations={
                "transcripts": [
                    {"transcript": "NM_3.1", "hgnc_id": 3},  # In one genepanel
                    {"transcript": "NM_3", "hgnc_id": 3},  # In one genepanel, no version
                    {
                        "transcript": "NM_2.2",
                        "hgnc_id": 2,
                    },  # In two genepanels, different version in one
                    {"transcript": "NM_NOT_IN_PANEL.1", "hgnc_id": 1},  # Not in any genepanel
                    {
                        "transcript": "NM_NOT_IN_PANEL",
                        "hgnc_id": 2,
                    },  # Not in any genepanel, no version
                ]
            },
        )

        a3, _ = mock_allele_with_annotation(
            session,
            annotations={
                "transcripts": [
                    {"transcript": "NM_1.2", "hgnc_id": 1},
                    {"transcript": "NM_1.3", "hgnc_id": 1},
                    {"transcript": "NM_2.1", "hgnc_id": 2},
                    {"transcript": "NM_2.2", "hgnc_id": 2},
                    {"transcript": "NM_3.1_sometext", "hgnc_id": 3},
                    {"transcript": "NM_3.2", "hgnc_id": 3},
                    {"transcript": "NM_3.3_sometext", "hgnc_id": 3},
                    {"transcript": "NM_3", "hgnc_id": 3},
                ]
            },
        )

        return a1, a2, a3

    a1, a2, a3 = insert_data()
    session.flush()

    annotation_transcripts_genepanel = queries.annotation_transcripts_genepanel(
        session, [("testpanel1", "v01"), ("testpanel2", "v01")]
    ).subquery()

    result = session.query(
        annotation_transcripts_genepanel.c.allele_id,
        annotation_transcripts_genepanel.c.name,
        annotation_transcripts_genepanel.c.version,
        annotation_transcripts_genepanel.c.annotation_transcript,
        annotation_transcripts_genepanel.c.genepanel_transcript,
    ).all()

    passes = [
        # allele_id, panel, annotation, genepanel
        (a1.id, "testpanel1", "v01", "NM_1.1", "NM_1.1"),
        (a1.id, "testpanel1", "v01", "NM_2.2", "NM_2.1"),
        (a1.id, "testpanel2", "v01", "NM_2.2", "NM_2.2"),
        (a2.id, "testpanel1", "v01", "NM_2.2", "NM_2.1"),
        (a2.id, "testpanel2", "v01", "NM_2.2", "NM_2.2"),
        (a2.id, "testpanel2", "v01", "NM_3.1", "NM_3.1"),
        (a3.id, "testpanel1", "v01", "NM_1.3", "NM_1.1"),
        (a3.id, "testpanel1", "v01", "NM_2.1", "NM_2.1"),
        (a3.id, "testpanel2", "v01", "NM_2.2", "NM_2.2"),
        (a3.id, "testpanel2", "v01", "NM_3.3_sometext", "NM_3.1"),
    ]

    assert set(result) == set(passes)

    session.rollback()
