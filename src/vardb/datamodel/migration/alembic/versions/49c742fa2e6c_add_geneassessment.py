"""Add geneassessment

Revision ID: 49c742fa2e6c
Revises: 2aabb5bc9e0c
Create Date: 2020-06-09 13:08:17.175461

"""

# revision identifiers, used by Alembic.
revision = "49c742fa2e6c"
down_revision = "2aabb5bc9e0c"
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


def upgrade():
    op.create_table(
        "geneassessment",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("evaluation", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("usergroup_id", sa.Integer(), nullable=True),
        sa.Column("date_created", sa.DateTime(timezone=True), nullable=False),
        sa.Column("genepanel_name", sa.String(), nullable=False),
        sa.Column("genepanel_version", sa.String(), nullable=False),
        sa.Column("date_superceeded", sa.DateTime(timezone=True), nullable=True),
        sa.Column("previous_assessment_id", sa.Integer(), nullable=True),
        sa.Column("gene_id", sa.Integer(), nullable=False),
        sa.Column("analysis_id", sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(
            ["analysis_id"], ["analysis.id"], name=op.f("fk_geneassessment_analysis_id_analysis")
        ),
        sa.ForeignKeyConstraint(
            ["gene_id"], ["gene.hgnc_id"], name=op.f("fk_geneassessment_gene_id_gene")
        ),
        sa.ForeignKeyConstraint(
            ["previous_assessment_id"],
            ["geneassessment.id"],
            name=op.f("fk_geneassessment_previous_assessment_id_geneassessment"),
        ),
        sa.ForeignKeyConstraint(
            ["user_id"], ["user.id"], name=op.f("fk_geneassessment_user_id_user")
        ),
        sa.ForeignKeyConstraint(
            ["usergroup_id"],
            ["usergroup.id"],
            name=op.f("fk_geneassessment_usergroup_id_usergroup"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_geneassessment")),
    )
    op.create_index(
        "ix_geneassessment_geneid_unique",
        "geneassessment",
        ["gene_id"],
        unique=True,
        postgresql_where=sa.text("date_superceeded IS NULL"),
    )


def downgrade():
    op.drop_index("ix_geneassessment_geneid_unique", table_name="geneassessment")
    op.drop_table("geneassessment")
