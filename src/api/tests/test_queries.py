from sqlalchemy import tuple_
from api.util import queries
from vardb.datamodel import gene, allele, annotation


def test_ad_genes_for_genepanel(session):

    testpanels = [
        ('HBOCUTV', 'v01'),
        ('OMIM', 'v01')
    ]

    for panel in testpanels:

        ad_genes = queries.ad_genes_for_genepanel(session, panel[0], panel[1]).all()
        ad_genes = [a[0] for a in ad_genes]

        # Test that AD matches only has 'AD' phenotypes
        inheritances = session.query(
            gene.Phenotype.inheritance
        ).join(
            gene.Gene,
            gene.Genepanel
        ).filter(
            tuple_(gene.Genepanel.name, gene.Genepanel.version) == panel,
            gene.Gene.hgnc_symbol.in_(ad_genes)
        ).all()
        assert all(i[0] == 'AD' for i in inheritances)

        # Test opposite case: non-AD genes has at least one non-AD phenotype
        inheritances = session.query(
            gene.Phenotype.gene_id,
            gene.Phenotype.inheritance
        ).join(
            gene.Gene,
            gene.Genepanel
        ).filter(
            tuple_(gene.Genepanel.name, gene.Genepanel.version) == panel,
            ~gene.Gene.hgnc_symbol.in_(ad_genes)
        ).all()

        gene_ids = set([i[0] for i in inheritances])
        for gene_id in gene_ids:
            gene_inheritances = [i[1] for i in inheritances if i[0] == gene_id]
            assert any(i != 'AD' for i in gene_inheritances)


def test_annotation_transcripts_genepanel(session):

    def insert_data():

        g1 = gene.Gene(hgnc_id=1, hgnc_symbol="GENE1")
        g2 = gene.Gene(hgnc_id=2, hgnc_symbol="GENE2")
        g3 = gene.Gene(hgnc_id=3, hgnc_symbol="GENE3")

        t1 = gene.Transcript(
            gene=g1,
            transcript_name='NM_1.1',
            type='RefSeq',
            genome_reference='123',
            chromosome='123',
            tx_start=123,
            tx_end=123,
            strand='+',
            cds_start=123,
            cds_end=123,
            exon_starts=[123, 321],
            exon_ends=[123, 321]
        )

        t2 = gene.Transcript(
            gene=g2,
            transcript_name='NM_2.1',
            type='RefSeq',
            genome_reference='123',
            chromosome='123',
            tx_start=123,
            tx_end=123,
            strand='+',
            cds_start=123,
            cds_end=123,
            exon_starts=[123, 321],
            exon_ends=[123, 321]
        )

        t3 = gene.Transcript(
            gene=g3,
            transcript_name='NM_3.1',
            type='RefSeq',
            genome_reference='123',
            chromosome='123',
            tx_start=123,
            tx_end=123,
            strand='+',
            cds_start=123,
            cds_end=123,
            exon_starts=[123, 321],
            exon_ends=[123, 321]
        )

        genepanel1 = gene.Genepanel(
            name='testpanel1',
            version='v01',
            genome_reference='GRCh37'
        )
        genepanel1.transcripts = [t1, t2]
        genepanel1.phenotypes = []
        session.add(genepanel1)

        genepanel2 = gene.Genepanel(
            name='testpanel2',
            version='v01',
            genome_reference='GRCh37'
        )

        genepanel2.transcripts = [t2, t3]
        genepanel1.phenotypes = []
        session.add(genepanel2)

        a1 = allele.Allele(
            genome_reference="GRCh37",
            chromosome="1",
            start_position=1,
            open_end_position=2,
            change_from="A",
            change_to="T",
            change_type="SNP",
            vcf_pos=1,
            vcf_ref="A",
            vcf_alt="T"
        )

        annotations = {
            'transcripts': [
                {
                    'transcript': 'NM_1.1'  # In genepanel
                },
                {
                    'transcript': 'NM_1'  # In genepanel, no version
                },
                {
                    'transcript': 'NM_2.2'  # In genepanel, different version
                },
                {
                    'transcript': 'NM_NOT_IN_PANEL.1'  # Not in genepanel
                },
                {
                    'transcript': 'NM_NOT_IN_PANEL'  # Not in genepanel, no version
                }
            ]
        }
        anno1 = annotation.Annotation(
            annotations=annotations,
            allele=a1
        )
        session.add(anno1)

        a2 = allele.Allele(
            genome_reference="GRCh37",
            chromosome="1",
            start_position=2,
            open_end_position=3,
            change_from="A",
            change_to="T",
            change_type="SNP",
            vcf_pos=2,
            vcf_ref="A",
            vcf_alt="T"
        )

        annotations = {
            'transcripts': [
                {
                    'transcript': 'NM_3.1'  # In one genepanel
                },
                {
                    'transcript': 'NM_3'  # In one genepanel, no version
                },
                {
                    'transcript': 'NM_2.2'  # In two genepanels, different version
                },
                {
                    'transcript': 'NM_NOT_IN_PANEL.1'  # Not in any genepanel
                },
                {
                    'transcript': 'NM_NOT_IN_PANEL'  # Not in any genepanel, no version
                }
            ]
        }
        anno2 = annotation.Annotation(
            annotations=annotations,
            allele=a2
        )
        session.add(anno2)

        return a1, a2

    a1, a2 = insert_data()
    session.flush()

    annotation_transcripts_genepanel = queries.annotation_transcripts_genepanel(
        session,
        [a1.id, a2.id],
        [('testpanel1', 'v01'), ('testpanel2', 'v01')]
    ).subquery()

    result = session.query(
        annotation_transcripts_genepanel.c.allele_id,
        annotation_transcripts_genepanel.c.name,
        annotation_transcripts_genepanel.c.version,
        annotation_transcripts_genepanel.c.annotation_transcript,
        annotation_transcripts_genepanel.c.genepanel_transcript
    ).all()

    passes = [
        # allele_id, panel, annotation, genepanel
        (a1.id, 'testpanel1', 'v01', 'NM_1.1', 'NM_1.1'),
        (a1.id, 'testpanel1', 'v01', 'NM_1', 'NM_1.1'),
        (a1.id, 'testpanel1', 'v01', 'NM_2.2', 'NM_2.1'),
        (a1.id, 'testpanel2', 'v01', 'NM_2.2', 'NM_2.1'),
        (a2.id, 'testpanel1', 'v01', 'NM_2.2', 'NM_2.1'),
        (a2.id, 'testpanel2', 'v01', 'NM_2.2', 'NM_2.1'),
        (a2.id, 'testpanel2', 'v01', 'NM_3.1', 'NM_3.1'),
        (a2.id, 'testpanel2', 'v01', 'NM_3', 'NM_3.1'),
    ]

    fails = [  # Same transcript name fail on both alleles
        'NM_NOT_IN_PANEL.1',
        'NM_NOT_IN_PANEL'
    ]

    for r in result:
        if not r[3].startswith('NM_NOT'):
            assert next((p for p in passes if r == p), None)
        else:
            assert r[3] in fails

    session.rollback()