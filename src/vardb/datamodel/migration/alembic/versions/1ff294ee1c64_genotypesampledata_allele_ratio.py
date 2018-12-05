"""genotypesampledata allele_ratio

Revision ID: 1ff294ee1c64
Revises: 250c9c10baee
Create Date: 2018-10-22 17:56:30.684035

"""

# revision identifiers, used by Alembic.
revision = '1ff294ee1c64'
down_revision = '250c9c10baee'
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa
from sqlalchemy.sql import column, table
from sqlalchemy.dialects import postgresql


def upgrade():
    op.add_column(u'genotypesampledata', sa.Column('allele_ratio', sa.Float(), nullable=True))
    # Migrating the existing data isn't necessary and would be error prone


def downgrade():
    raise NotImplementedError('Downgrade not possible')
