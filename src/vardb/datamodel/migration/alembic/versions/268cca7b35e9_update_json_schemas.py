"""Update json schemas

Revision ID: 268cca7b35e9
Revises: 92b582acebc6
Create Date: 2020-04-06 11:14:56.666185

"""

# revision identifiers, used by Alembic.
revision = "268cca7b35e9"
down_revision = "92b582acebc6"
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa
from sqlalchemy.orm.session import Session
from vardb.datamodel.jsonschemas.update_schemas import update_schemas


def upgrade():
    # Filterconfig and annotations schemas are updated, but is fully backward compatible. Therefore, replace the existing
    # schemas (should only be one per), by first dropping it, and update_schemas again
    op.execute("DELETE FROM jsonschema WHERE name in ('filterconfig', 'annotation') and version=1")
    session = Session(bind=op.get_bind())
    update_schemas(session)
    session.flush()


def downgrade():
    raise NotImplementedError()
