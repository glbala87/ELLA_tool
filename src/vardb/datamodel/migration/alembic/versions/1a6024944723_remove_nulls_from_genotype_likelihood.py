"""Remove nulls from genotype_likelihood

Revision ID: 1a6024944723
Revises: 611d46cd83b4
Create Date: 2021-05-03 10:40:21.612629

"""

# revision identifiers, used by Alembic.
revision = "1a6024944723"
down_revision = "611d46cd83b4"
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa


def upgrade():
    conn = op.get_bind()

    conn.execute(
        sa.sql.text(
            "UPDATE genotypesampledata SET genotype_likelihood=array_remove(genotype_likelihood, NULL);"
        )
    )

    conn.execute(
        sa.sql.text(
            "UPDATE genotypesampledata SET genotype_likelihood=NULL WHERE genotype_likelihood='{}';"
        )
    )
    op.create_check_constraint(
        "genotypesampledata_genotype_likelihood_check",
        "genotypesampledata",
        "array_position(genotype_likelihood, NULL) is NULL",
    )


def downgrade():
    # Not strictly downgradeable, but changes are consistent with earlier migrations
    pass
