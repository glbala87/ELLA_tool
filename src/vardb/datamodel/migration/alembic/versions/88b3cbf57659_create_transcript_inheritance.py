"""Create transcript inheritance

Revision ID: 88b3cbf57659
Revises: 1675e8d8b078
Create Date: 2023-02-14 10:19:42.569913

"""

# revision identifiers, used by Alembic.
revision = "88b3cbf57659"
down_revision = "1675e8d8b078"
branch_labels = None
depends_on = None

from typing import Set

from alembic import op


def compute_consensus_inheritance(inheritances: Set[str]):
    if inheritances == {"AD"}:
        return "AD"
    elif inheritances == {"AR"}:
        return "AR"
    elif inheritances == {"XD"}:
        return "XD"
    elif inheritances == {"XR"}:
        return "XR"
    elif any(inh.startswith("X") for inh in inheritances):
        return "XD/XR"
    return "AD/AR"


def distinct_inheritance_hgnc_ids(conn, genepanel_name, genepanel_version, inheritance):
    "Equal to queries.distinct_inheritance_hgnc_ids at time of writing"
    res = conn.execute(
        f"""
        SELECT phenotype.gene_id AS hgnc_id
        FROM phenotype, genepanel_phenotype AS gp_phenotype
        WHERE phenotype.id = gp_phenotype.phenotype_id
        AND gp_phenotype.genepanel_name = '{genepanel_name}'
        AND gp_phenotype.genepanel_version = '{genepanel_version}'
        GROUP BY gp_phenotype.genepanel_name, gp_phenotype.genepanel_version, phenotype.gene_id
        HAVING every(phenotype.inheritance = '{inheritance}')
        """
    ).fetchall()

    return set([r[0] for r in res])


def upgrade():
    # Loop over all gene panels
    # For each gene panel, loop over all transcripts
    # For each gene in gene panel, get all phenotypes
    # Compute consensus inheritance
    # Add consensus inheritance to genepanel_transcript entry
    conn = op.get_bind()
    conn.execute("ALTER TABLE genepanel_transcript ADD COLUMN inheritance text")

    genepanels = conn.execute("SELECT name, version FROM genepanel").fetchall()

    for genepanel_name, genepanel_version in genepanels:
        # Update genepanel_transcript table with consensus inheritance
        # from genepanel phenotypes for each gene
        hgnc_id_inheritances = conn.execute(
            f"""
            SELECT gene_id, array_agg(inheritance) FROM phenotype WHERE id IN (
                SELECT DISTINCT phenotype_id
                FROM genepanel_phenotype
                WHERE genepanel_name = '{genepanel_name}'
                AND genepanel_version = '{genepanel_version}'
            )
            GROUP BY gene_id
            """,
        ).fetchall()

        hgnc_id_transcript_ids = conn.execute(
            f"""
            SELECT gene_id, id FROM transcript WHERE id IN (
                SELECT DISTINCT transcript_id
                FROM genepanel_transcript
                WHERE genepanel_name = '{genepanel_name}'
                AND genepanel_version = '{genepanel_version}'
            )
            """,
        ).fetchall()

        inheritance_by_hgnc_id = dict(hgnc_id_inheritances)
        new_ad_genes = set()
        new_ar_genes = set()
        for hgnc_id, transcript_id in hgnc_id_transcript_ids:
            consensus_inheritance = compute_consensus_inheritance(
                set(inheritance_by_hgnc_id.get(hgnc_id, []))
            )
            if consensus_inheritance == "AD":
                new_ad_genes.add(hgnc_id)
            elif consensus_inheritance == "AR":
                new_ar_genes.add(hgnc_id)

            conn.execute(
                f"""
                UPDATE genepanel_transcript SET inheritance = '{consensus_inheritance}'
                WHERE transcript_id = '{transcript_id}'
                AND genepanel_name = '{genepanel_name}'
                AND genepanel_version = '{genepanel_version}'
                """
            )

            legacy_ad_genes = distinct_inheritance_hgnc_ids(
                conn, genepanel_name, genepanel_version, "AD"
            )
            legacy_ar_genes = distinct_inheritance_hgnc_ids(
                conn, genepanel_name, genepanel_version, "AR"
            )

        assert legacy_ad_genes == new_ad_genes
        assert legacy_ar_genes == new_ar_genes

    conn.execute("ALTER TABLE genepanel_transcript ALTER COLUMN inheritance SET NOT NULL")
    conn.execute("ALTER TABLE transcript ADD COLUMN source text NOT NULL DEFAULT ('Ensembl')")


def downgrade():
    conn = op.get_bind()
    conn.execute("ALTER TABLE genepanel_transcript DROP COLUMN inheritance")
