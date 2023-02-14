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

import hashlib
from typing import Set

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql
from sqlalchemy.orm.session import Session
from sqlalchemy.sql import column, table


# Genepanel = table("genepanel", column("name", sa.String()), column("version", sa.String()))
def compute_consensus_inheritance(inheritances: Set[str]):
    if inheritances == {"AD"}:
        return "AD"
    elif inheritances == {"AR"}:
        return "AR"
    elif inheritances == {"XD"}:
        return "XD"
    elif inheritances == {"XR"}:
        return "XR"
    return "AD/AR"


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
        # Update genepanel_transcript table

        print(genepanel_name, genepanel_version)

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
        for hgnc_id, transcript_id in hgnc_id_transcript_ids:
            if hgnc_id in inheritance_by_hgnc_id:
                consensus_inheritance = compute_consensus_inheritance(
                    set(inheritance_by_hgnc_id[hgnc_id])
                )
            else:
                consensus_inheritance = "N/A"
            conn.execute(
                f"""
                UPDATE genepanel_transcript SET inheritance = '{consensus_inheritance}'
                WHERE transcript_id = '{transcript_id}'
                AND genepanel_name = '{genepanel_name}'
                AND genepanel_version = '{genepanel_version}'
                """
            )
        print(
            conn.execute(
                f"""
                SELECT inheritance, count(*) FROM genepanel_transcript
                WHERE genepanel_name = '{genepanel_name}'
                AND genepanel_version = '{genepanel_version}'
                GROUP BY inheritance
                """
            ).fetchall()
        )

    conn.execute("ALTER TABLE genepanel_transcript ALTER COLUMN inheritance text NOT NULL")

    raise RuntimeError()


def downgrade():
    conn = op.get_bind()
    conn.execute("ALTER TABLE genepanel_transcript DROP COLUMN inheritance")
