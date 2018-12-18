"""Hash access token

Revision ID: 86deaf190356
Revises: 780575a06f97
Create Date: 2018-06-25 12:55:54.036192

"""

# revision identifiers, used by Alembic.
revision = "86deaf190356"
down_revision = "780575a06f97"
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa
from sqlalchemy.sql import table, column
from sqlalchemy.dialects import postgresql
import hashlib

UserSession = table("usersession", column("id", sa.Integer), column("token", sa.String()))


def upgrade():
    conn = op.get_bind()
    tokens = conn.execute(sa.select([UserSession.c.id, UserSession.c.token]))

    for t in tokens:
        conn.execute(
            sa.update(UserSession)
            .where(UserSession.c.id == t.id)
            .values({"token": hashlib.sha256(t.token).hexdigest()})
        )


def downgrade():
    raise NotImplementedError("Downgrade not possible")
