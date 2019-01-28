"""Add cli log

Revision ID: 99287295d7fe
Revises: ec5fb8b62e4a
Create Date: 2019-01-04 09:34:32.410610

"""

# revision identifiers, used by Alembic.
revision = "99287295d7fe"
down_revision = "2a1becd831ab"
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.create_table(
        "clilog",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("time", sa.DateTime(timezone=True), nullable=False),
        sa.Column("user", sa.String(), nullable=False),
        sa.Column("group", sa.String(), nullable=False),
        sa.Column("groupcommand", sa.String(), nullable=False),
        sa.Column("command", sa.String(), nullable=False),
        sa.Column("reason", sa.String()),
        sa.Column("output", sa.String(), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_clilog")),
    )


def downgrade():
    op.drop_table("clilog")
