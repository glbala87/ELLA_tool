"""Add classification filter to snapshot

Revision ID: 12760875ee2d
Revises: 022118518e99
Create Date: 2019-03-20 09:51:27.563531

"""

# revision identifiers, used by Alembic.
revision = "12760875ee2d"
down_revision = "022118518e99"
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa
from vardb.datamodel.migration.utils import update_enum

TABLE_NAMES = ["alleleinterpretationsnapshot", "analysisinterpretationsnapshot"]
OLD_OPTIONS = [
    "FREQUENCY",
    "REGION",
    "POLYPYRIMIDINE",
    "GENE",
    "QUALITY",
    "CONSEQUENCE",
    "SEGREGATION",
    "INHERITANCEMODEL",
]

NEW_OPTIONS = OLD_OPTIONS + ["CLASSIFICATION"]


def upgrade():
    # Update snapshot tables
    with update_enum(
        op, TABLE_NAMES, "filtered", "interpretationsnapshot_filtered", OLD_OPTIONS, NEW_OPTIONS
    ) as tmp_tables:
        # We don't need to convert enums, we're only adding new ones
        pass


def downgrade():
    raise RuntimeError("Downgrade not supported")
