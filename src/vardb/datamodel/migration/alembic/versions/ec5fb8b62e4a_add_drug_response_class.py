"""Add drug response class

Revision ID: ec5fb8b62e4a
Revises: 1ff294ee1c64
Create Date: 2018-12-05 09:49:41.400476

"""

# revision identifiers, used by Alembic.
revision = "ec5fb8b62e4a"
down_revision = "1ff294ee1c64"
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa
from vardb.datamodel.migration.utils import update_enum
from sqlalchemy.dialects import postgresql

TABLE_NAMES = ["alleleassessment"]
OLD_OPTIONS = [u"1", u"2", u"3", u"4", u"5", u"U"]
NEW_OPTIONS = OLD_OPTIONS + [u"DR"]


def upgrade():
    # Update snapshot tables
    with update_enum(
        op,
        TABLE_NAMES,
        "classification",
        "alleleassessment_classification",
        OLD_OPTIONS,
        NEW_OPTIONS,
    ) as tmp_tables:
        # We don't need to convert enums, we're only adding new ones
        pass


def downgrade():
    raise RuntimeError("Downgrade not supported")
