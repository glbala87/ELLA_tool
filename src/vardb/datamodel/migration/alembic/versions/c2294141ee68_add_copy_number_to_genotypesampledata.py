"""Add copy_number to genotypesampledata

Revision ID: c2294141ee68
Revises: fa9687c3fd90
Create Date: 2021-09-07 10:30:52.365687

"""

# revision identifiers, used by Alembic.
revision = "c2294141ee68"
down_revision = "fa9687c3fd90"
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.add_column("genotypesampledata", sa.Column("copy_number", sa.SmallInteger(), nullable=True))


def downgrade():
    op.drop_column("genotypesampledata", "copy_number")
