"""Add polypyrimidine to interpretationsnapsho

Revision ID: 250c9c10baee
Revises: 4629b478b291
Create Date: 2018-11-05 09:57:17.975367

"""

# revision identifiers, used by Alembic.
revision = '250c9c10baee'
down_revision = '4629b478b291'
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from vardb.datamodel.migration.utils import update_enum

TABLE_NAMES = ['alleleinterpretationsnapshot', 'analysisinterpretationsnapshot']
OLD_OPTIONS = ['GENE', 'FREQUENCY', 'REGION', 'QUALITY', 'SEGRETATION']
NEW_OPTIONS = OLD_OPTIONS + ['POLYPYRIMIDINE']

def upgrade():
    # Update snapshot tables
    with update_enum(op, TABLE_NAMES, 'filtered', 'interpretationsnapshot_filtered', OLD_OPTIONS, NEW_OPTIONS) as tmp_tables:
        # We don't need to convert enums, we're only adding new ones
        pass

def downgrade():
    raise RuntimeError("Downgrade not supported")
