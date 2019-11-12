"""Replace filterconfig schema

Revision ID: 0cefb5c63c6d
Revises: d6290a3fdf7b
Create Date: 2019-11-12 08:28:09.119801

"""

# revision identifiers, used by Alembic.
revision = "0cefb5c63c6d"
down_revision = "d6290a3fdf7b"
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa
from sqlalchemy.orm.session import Session
from vardb.datamodel.jsonschemas.update_schemas import update_schemas
from vardb.datamodel.migration.utils import update_enum

TABLE_NAMES = ["alleleinterpretationsnapshot", "analysisinterpretationsnapshot"]

OLD_OPTIONS = [
    "CLASSIFICATION",
    "FREQUENCY",
    "REGION",
    "POLYPYRIMIDINE",
    "GENE",
    "QUALITY",
    "CONSEQUENCE",
    "SEGREGATION",
    "INHERITANCEMODEL",
]
NEW_OPTIONS = OLD_OPTIONS + ["QUALITYAR", "QUALITYFILTER", "QUALITYQUAL"]


def upgrade():
    with update_enum(
        op, TABLE_NAMES, "filtered", "interpretationsnapshot_filtered", OLD_OPTIONS, NEW_OPTIONS
    ) as tmp_tables:
        # We don't need to convert enums, we're only adding new ones
        pass

    # Filterconfig schema is updated, but is fully backward compatible. Therefore, replace the existing
    # schemas (should be only one), by first dropping it, and update_schemas again
    op.execute("DELETE FROM jsonschema WHERE name='filterconfig' and version=1")
    session = Session(bind=op.get_bind())
    update_schemas(session)
    session.flush()


def downgrade():
    raise NotImplementedError()
