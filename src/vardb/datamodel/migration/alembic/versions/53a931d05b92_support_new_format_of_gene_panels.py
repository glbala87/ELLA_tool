"""Support new format of gene panels

Revision ID: 53a931d05b92
Revises: 1675e8d8b078
Create Date: 2022-02-03 08:15:43.980374

"""

# revision identifiers, used by Alembic.
revision = "53a931d05b92"
down_revision = "1675e8d8b078"
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.add_column("transcript", sa.Column("inheritance", sa.String(), nullable=True))
    op.add_column("transcript", sa.Column("source", sa.String(), nullable=True))
    op.drop_constraint("uq_transcript_transcript_name", "transcript", type_="unique")
    op.create_unique_constraint(
        op.f("uq_transcript_transcript_name"), "transcript", ["transcript_name", "inheritance"]
    )


def downgrade():
    op.drop_constraint(op.f("uq_transcript_transcript_name"), "transcript", type_="unique")
    op.create_unique_constraint("uq_transcript_transcript_name", "transcript", ["transcript_name"])
    op.drop_column("transcript", "source")
    op.drop_column("transcript", "inheritance")
