"""Remove filterconfig enums

Revision ID: 92b582acebc6
Revises: fa3bc78eb17b
Create Date: 2020-02-14 11:42:32.464331

"""

# revision identifiers, used by Alembic.
revision = "92b582acebc6"
down_revision = "fa3bc78eb17b"
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa
from sqlalchemy.orm.session import Session
from vardb.datamodel.jsonschemas.update_schemas import update_schemas


def upgrade():
    # Filterconfig schemas are updated, but is fully backward compatible. Therefore, replace the existing
    # schemas (should only be one per), by first dropping it, and update_schemas again
    op.execute("DELETE FROM jsonschema WHERE name in ('filterconfig', 'annotation') and version=1")
    session = Session(bind=op.get_bind())
    update_schemas(session)
    session.flush()


def downgrade():
    raise NotImplementedError("Downgrade not supported")
