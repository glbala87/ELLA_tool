"""Add inheritancemodel to enum

Revision ID: 2a1becd831ab
Revises: ec5fb8b62e4a
Create Date: 2019-01-18 08:44:11.434039

"""

# revision identifiers, used by Alembic.
revision = "2a1becd831ab"
down_revision = "ec5fb8b62e4a"
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa

from vardb.datamodel.migration.utils import update_enum

TABLE_NAMES = ["alleleinterpretationsnapshot", "analysisinterpretationsnapshot"]
OLD_OPTIONS = [
    "GENE",
    "FREQUENCY",
    "REGION",
    "QUALITY",
    "SEGRETATION",
    "POLYPYRIMIDINE",
    "CONSEQUENCE",
]
NEW_OPTIONS = OLD_OPTIONS + ["INHERITANCEMODEL"]


def upgrade():
    # Update snapshot tables
    with update_enum(
        op, TABLE_NAMES, "filtered", "interpretationsnapshot_filtered", OLD_OPTIONS, NEW_OPTIONS
    ) as tmp_tables:
        # We don't need to convert enums, we're only adding new ones
        pass


def downgrade():
    raise RuntimeError("Downgrade not supported")
