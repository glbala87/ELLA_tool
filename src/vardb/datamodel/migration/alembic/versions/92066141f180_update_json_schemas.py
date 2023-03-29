"""Update json schemas

Revision ID: 92066141f180
Revises: 88b3cbf57659
Create Date: 2023-03-03 12:22:32.686142

"""

# revision identifiers, used by Alembic.
revision = "92066141f180"
down_revision = "88b3cbf57659"
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa
from sqlalchemy.orm.session import Session
from vardb.datamodel.jsonschemas.update_schemas import update_schemas


def upgrade():
    # Filterconfig and annotations schemas are updated, but is fully backward compatible. Therefore, replace the existing
    # schemas by first dropping it, and update_schemas again
    op.execute(
        "DELETE FROM jsonschema WHERE (name ='filterconfig' and version=3) OR (name='annotation' and version=1)"
    )
    session = Session(bind=op.get_bind())
    update_schemas(session)
    session.flush()


def downgrade():
    raise NotImplementedError()
