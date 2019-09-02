"""Add genotypesampledata-genotype_id index

Revision ID: 96bec57f81de
Revises: 529e8f6faed9
Create Date: 2019-09-02 07:31:44.971462

"""

# revision identifiers, used by Alembic.
revision = "96bec57f81de"
down_revision = "529e8f6faed9"
branch_labels = None
depends_on = None

from alembic import op


def upgrade():
    op.create_index(
        op.f("ix_genotypesampledata_genotype_id"),
        "genotypesampledata",
        ["genotype_id"],
        unique=False,
    )


def downgrade():
    op.drop_index(op.f("ix_genotypesampledata_genotype_id"), table_name="genotypesampledata")
