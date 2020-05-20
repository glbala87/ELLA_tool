"""Open end position

Revision ID: 2aabb5bc9e0c
Revises: 268cca7b35e9
Create Date: 2020-04-28 07:33:36.714604

"""

# revision identifiers, used by Alembic.
revision = "2aabb5bc9e0c"
down_revision = "268cca7b35e9"
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa


def upgrade():
    conn = op.get_bind()

    conn.execute(
        sa.sql.text(
            "UPDATE allele SET open_end_position=start_position, start_position=start_position-1 WHERE change_type='ins';"
        )
    )

    conn.execute(
        sa.sql.text(
            "UPDATE allele SET open_end_position=start_position+length(change_from) WHERE change_type='indel';"
        )
    )


def downgrade():
    raise NotImplementedError("Downgrade not possible")
