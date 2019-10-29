"""Replace filterconfig schema

Revision ID: 4dee968751a0
Revises: 96bec57f81de
Create Date: 2019-10-14 07:54:04.855429

"""

# revision identifiers, used by Alembic.
revision = "4dee968751a0"
down_revision = "96bec57f81de"
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
