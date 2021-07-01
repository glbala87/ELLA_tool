"""add length column to allele

Revision ID: 159bc8c35c00
Revises: ae39a6819b47
Create Date: 2021-02-16 13:06:25.111748

"""

# revision identifiers, used by Alembic.
revision = "159bc8c35c00"
down_revision = "d394766ada41"
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa


def upgrade():
    conn = op.get_bind()

    op.add_column("allele", sa.Column("length", sa.Integer(), nullable=True))

    """
    This must resemble the way length is calculated in Python, as of time being this is
    done in: vcfiterator.py, inside the function:

    def _snv_allele_info(self, pos, ref, alt):
    """

    conn.execute(
        sa.sql.text(
            "UPDATE allele SET length=(GREATEST(length(change_from),length(change_to))) WHERE change_type != 'ins';"
        )
    )

    conn.execute(sa.sql.text("UPDATE allele SET length=1 WHERE change_type = 'ins' ;"))
    op.alter_column("allele", "length", nullable=False)


def downgrade():
    conn = op.get_bind()
    op.drop_column("allele", sa.Column("length"))
