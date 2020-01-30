"""Resourcelog time index

Revision ID: fa3bc78eb17b
Revises: 93e88dd283a2
Create Date: 2020-01-28 12:57:44.213493

"""

# revision identifiers, used by Alembic.
revision = "fa3bc78eb17b"
down_revision = "93e88dd283a2"
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.create_index(op.f("ix_resourcelog_time"), "resourcelog", ["time"], unique=False)


def downgrade():
    op.drop_index(op.f("ix_resourcelog_time"), table_name="resourcelog")
