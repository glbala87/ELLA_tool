from sqlalchemy import func, tuple_
from datalayer import queries
from vardb.datamodel import gene
from conftest import mock_allele_with_annotation


def test_distinct_inheritance_hgnc_ids_for_genepanel(session):
    testpanels = session.query(gene.Genepanel.name, gene.Genepanel.version).all()
    inheritance_modes = ["AR", "AD"]

    for panel in testpanels:
        for inheritance_mode in inheritance_modes:
            hgnc_ids = queries.distinct_inheritance_hgnc_ids_for_genepanel(
                session, inheritance_mode, panel[0], panel[1]
            ).scalar_all()

            # Check that hgnc ids are subset of all gene panel hgnc ids
            all_hgnc_ids = (
                session.query(
                    gene.Transcript.gene_id,
                )
                .join(gene.genepanel_transcript)
                .filter(
                    gene.genepanel_transcript.c.genepanel_name == panel[0],
                    gene.genepanel_transcript.c.genepanel_version == panel[1],
                )
            ).scalar_all()

            assert set(hgnc_ids).issubset(all_hgnc_ids)

            # Collect inheritance for all transcripts and phenotypes in gene panel
            genepanel_tx_inheritance = (
                session.query(
                    gene.Transcript.gene_id,
                    func.array_agg(gene.Transcript.inheritance).label("tx_inheritance"),
                )
                .join(gene.genepanel_transcript)
                .filter(
                    tuple_(
                        gene.genepanel_transcript.c.genepanel_name,
                        gene.genepanel_transcript.c.genepanel_version,
                    )
                    == panel
                )
                .group_by(gene.Transcript.gene_id)
            ).all()

            genepanel_tx_inheritance = {k: set(v) for k, v in genepanel_tx_inheritance}

            genepanel_phenotype_inheritance = (
                session.query(
                    gene.Phenotype.gene_id,
                    func.array_agg(gene.Phenotype.inheritance).label("ph_inheritance"),
                )
                .join(gene.genepanel_phenotype)
                .filter(
                    tuple_(
                        gene.genepanel_phenotype.c.genepanel_name,
                        gene.genepanel_phenotype.c.genepanel_version,
                    )
                    == panel
                )
                .group_by(gene.Phenotype.gene_id)
            ).all()

            genepanel_phenotype_inheritance = {
                k: set(v) for k, v in genepanel_phenotype_inheritance
            }

            # Expect that hgnc ids in query satisify either:
            # a) inheritance matches all transcripts for hgnc id
            # b) no transcripts have inheritance for hgnc id, and inheritance matches all phenotypes for hgnc_id
            expected = set()
            for hgnc_id in all_hgnc_ids:
                if genepanel_tx_inheritance[hgnc_id] == set([inheritance_mode]):
                    # Matches at transcript level
                    expected.add(hgnc_id)
                    continue

                if genepanel_tx_inheritance[hgnc_id] == set(
                    [None]
                ) and genepanel_phenotype_inheritance[hgnc_id] == set([inheritance_mode]):
                    # No inheritance at transcript level, matches at phenotype level
                    expected.add(hgnc_id)
                    continue

                # Not expected, double check that it has a different inheritance
                assert genepanel_tx_inheritance[hgnc_id] != set([inheritance_mode])

                assert not (
                    genepanel_tx_inheritance[hgnc_id] == set([None])
                    and genepanel_phenotype_inheritance[hgnc_id] == set([inheritance_mode])
                )

            assert set(hgnc_ids) == expected


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

        t1 = gene.Transcript(gene=g1, transcript_name="NM_1.1", **transcript_base)

        t21 = gene.Transcript(gene=g2, transcript_name="NM_2.1", **transcript_base)

        t22 = gene.Transcript(gene=g2, transcript_name="NM_2.2", **transcript_base)

        t3 = gene.Transcript(gene=g3, transcript_name="NM_3.1", **transcript_base)

        genepanel1 = gene.Genepanel(name="testpanel1", version="v01.0", genome_reference="GRCh37")
        genepanel1.transcripts = [t1, t21]
        genepanel1.phenotypes = []
        session.add(genepanel1)

        genepanel2 = gene.Genepanel(name="testpanel2", version="v01.0", genome_reference="GRCh37")

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
        session, [("testpanel1", "v01.0"), ("testpanel2", "v01.0")]
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
        (a1.id, "testpanel1", "v01.0", "NM_1.1", "NM_1.1"),
        (a1.id, "testpanel1", "v01.0", "NM_2.2", "NM_2.1"),
        (a1.id, "testpanel2", "v01.0", "NM_2.2", "NM_2.2"),
        (a2.id, "testpanel1", "v01.0", "NM_2.2", "NM_2.1"),
        (a2.id, "testpanel2", "v01.0", "NM_2.2", "NM_2.2"),
        (a2.id, "testpanel2", "v01.0", "NM_3.1", "NM_3.1"),
        (a3.id, "testpanel1", "v01.0", "NM_1.3", "NM_1.1"),
        (a3.id, "testpanel1", "v01.0", "NM_2.1", "NM_2.1"),
        (a3.id, "testpanel2", "v01.0", "NM_2.2", "NM_2.2"),
        (a3.id, "testpanel2", "v01.0", "NM_3.3_sometext", "NM_3.1"),
    ]

    assert set(result) == set(passes)

    session.rollback()
