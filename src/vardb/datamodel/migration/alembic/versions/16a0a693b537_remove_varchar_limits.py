"""Remove varchar limits

Revision ID: 16a0a693b537
Revises: d6290a3fdf7b
Create Date: 2020-01-09 08:32:02.929036

"""

# revision identifiers, used by Alembic.
revision = "16a0a693b537"
down_revision = "d6290a3fdf7b"
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa


def upgrade():
    table_columns = [
        ("genepanel", "genome_reference"),
        ("gene", "ensembl_gene_id"),
        ("phenotype", "description"),
        ("phenotype", "inheritance"),
    ]
    for table, column in table_columns:
        op.execute(f"ALTER TABLE {table} ALTER COLUMN {column} TYPE varchar")


def downgrade():
    raise NotImplementedError("Downgrade not possible")
