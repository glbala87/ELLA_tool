"""Update allele unique constraint

Revision ID: 1675e8d8b078
Revises: c2294141ee68
Create Date: 2021-09-07 10:34:04.060963

"""

# revision identifiers, used by Alembic.
revision = "1675e8d8b078"
down_revision = "c2294141ee68"
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.drop_constraint("ucAllele", "allele", type_="unique")
    op.create_unique_constraint(
        "ucAllele",
        "allele",
        [
            "chromosome",
            "start_position",
            "open_end_position",
            "change_from",
            "change_to",
            "change_type",
            "vcf_pos",
            "vcf_ref",
            "vcf_alt",
            "length",
            "caller_type",
        ],
    )


def downgrade():
    op.drop_constraint("ucAllele", "allele", type_="unique")
    op.create_unique_constraint(
        "ucAllele",
        "allele",
        [
            "chromosome",
            "start_position",
            "open_end_position",
            "change_from",
            "change_to",
            "change_type",
            "vcf_pos",
            "vcf_ref",
            "vcf_alt",
        ],
    )
