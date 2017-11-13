from sqlalchemy import tuple_
from api.util import queries
from vardb.datamodel import gene


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
