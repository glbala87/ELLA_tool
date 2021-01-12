"""Add ui exception table

Revision ID: 924438596189
Revises: 0143c6e15141
Create Date: 2020-10-15 14:29:52.596394

"""

# revision identifiers, used by Alembic.
revision = "924438596189"
down_revision = "0143c6e15141"
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


def upgrade():
    op.create_table(
        "uiexception",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("time", sa.DateTime(timezone=True), nullable=False),
        sa.Column("usersession_id", sa.Integer(), nullable=True),
        sa.Column("message", sa.String(), nullable=False),
        sa.Column("location", sa.String(), nullable=True),
        sa.Column("stacktrace", sa.String(), nullable=True),
        sa.Column("state", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.ForeignKeyConstraint(
            ["usersession_id"],
            ["usersession.id"],
            name=op.f("fk_uiexception_usersession_id_usersession"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_uiexception")),
    )


def downgrade():
    op.drop_table("uiexception")
