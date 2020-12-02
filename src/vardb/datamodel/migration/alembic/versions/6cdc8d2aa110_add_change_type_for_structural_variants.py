"""add change_type for structural variants

Revision ID: 6cdc8d2aa110
Revises: 159bc8c35c00
Create Date: 2021-03-17 09:26:31.455061

"""

"""
Using this cookbook, along with postgres 11 docs
https://medium.com/makimo-tech-blog/upgrading-postgresqls-enum-type-with-sqlalchemy-using-alembic-migration-881af1e30abe
"""

# revision identifiers, used by Alembic.
revision = "6cdc8d2aa110"
down_revision = "159bc8c35c00"
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa


def upgrade():
    with op.get_context().autocommit_block():
        op.execute("ALTER TYPE change_type ADD VALUE 'dup' AFTER 'indel'")

    with op.get_context().autocommit_block():
        op.execute("ALTER TYPE change_type ADD VALUE 'dup_tandem' AFTER 'dup'")

    with op.get_context().autocommit_block():
        op.execute("ALTER TYPE change_type ADD VALUE 'del_me' AFTER 'dup_tandem'")

    with op.get_context().autocommit_block():
        op.execute("ALTER TYPE change_type ADD VALUE 'ins_me' AFTER 'del_me'")

    with op.get_context().autocommit_block():
        op.execute("ALTER TYPE change_type ADD VALUE 'inv' AFTER 'ins_me'")

    with op.get_context().autocommit_block():
        op.execute("ALTER TYPE change_type ADD VALUE 'bnd' AFTER 'inv'")


def downgrade():
    pass
