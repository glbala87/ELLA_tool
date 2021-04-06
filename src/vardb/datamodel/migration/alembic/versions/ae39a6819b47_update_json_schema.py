"""Update json schema

Revision ID: ae39a6819b47
Revises: 611d46cd83b4
Create Date: 2021-03-11 14:46:03.163712

"""

# revision identifiers, used by Alembic.
revision = "ae39a6819b47"
down_revision = "611d46cd83b4"
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa
from sqlalchemy.orm.session import Session
from vardb.datamodel.jsonschemas.update_schemas import update_schemas


def upgrade():
    # Filterconfig schema is updated, but is fully backward compatible. Therefore, replace the changed schema
    # by first dropping it, and update_schemas again
    op.execute("DELETE FROM jsonschema WHERE name='filterconfig' and version=3")
    session = Session(bind=op.get_bind())
    update_schemas(session)
    session.flush()


def downgrade():
    raise NotImplementedError()
