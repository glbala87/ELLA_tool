"""Redefine classification choices

Revision ID: d87c53d0e1d4
Revises: 0143c6e15141
Create Date: 2020-12-16 14:52:53.513976

"""

# revision identifiers, used by Alembic.
revision = "d87c53d0e1d4"
down_revision = "0143c6e15141"
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa
from vardb.datamodel.migration.utils import update_enum
from sqlalchemy.orm.session import Session
from vardb.datamodel.jsonschemas.update_schemas import update_schemas

OLD_CLASSIFICATIONS = ["1", "2", "3", "4", "5", "U", "DR"]
NEW_CLASSIFICATIONS = ["1", "2", "3", "4", "5", "NP", "DR", "RF"]


def upgrade():
    with update_enum(
        op,
        ["alleleassessment"],
        "classification",
        "alleleassessment_classification",
        OLD_CLASSIFICATIONS,
        NEW_CLASSIFICATIONS,
    ) as tmp_tables:
        conn = op.get_bind()
        # Replace class U with class NP
        conn.execute("UPDATE alleleassessment SET classification='NP' WHERE classification='U'")

    session = Session(bind=op.get_bind())
    update_schemas(session)
    session.flush()


def downgrade():
    raise NotImplementedError("Downgrade not supported")
