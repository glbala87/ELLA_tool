"""add_caller_type_column_to_allele.py

Revision ID: fa9687c3fd90
Revises: 6cdc8d2aa110
Create Date: 2021-05-27 08:21:18.901683

"""
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "fa9687c3fd90"
down_revision = "6cdc8d2aa110"
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa


def upgrade():
    conn = op.get_bind()

    caller_type = postgresql.ENUM("SNV", "CNV", name="caller_type")
    caller_type.create(conn)

    op.add_column(
        "allele", sa.Column("caller_type", sa.Enum("SNV", "CNV", name="caller_type"), nullable=True)
    )

    conn.execute(sa.sql.text("UPDATE allele SET caller_type = 'SNV';"))

    op.alter_column("allele", "caller_type", nullable=False)


def downgrade():
    conn = op.get_bind()
    op.drop_column("allele", sa.Column("caller_type"))
    conn.execute(sa.sql.text("DROP TYPE caller_type"))
