"""Add consequence to interpretationsnapshot

Revision ID: 1c5e523b57b3
Revises: 61b990b84ed2
Create Date: 2018-11-06 11:59:03.515917

"""

# revision identifiers, used by Alembic.
revision = "1c5e523b57b3"
down_revision = "61b990b84ed2"
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa
from vardb.datamodel.migration.utils import update_enum

TABLE_NAMES = ["alleleinterpretationsnapshot", "analysisinterpretationsnapshot"]
OLD_OPTIONS = ["GENE", "FREQUENCY", "REGION", "QUALITY", "SEGRETATION", "POLYPYRIMIDINE"]
NEW_OPTIONS = OLD_OPTIONS + ["CONSEQUENCE"]


def upgrade():
    # Update snapshot tables
    with update_enum(
        op, TABLE_NAMES, "filtered", "interpretationsnapshot_filtered", OLD_OPTIONS, NEW_OPTIONS
    ) as tmp_tables:
        # We don't need to convert enums, we're only adding new ones
        pass


def downgrade():
    raise RuntimeError("Downgrade not supported")
