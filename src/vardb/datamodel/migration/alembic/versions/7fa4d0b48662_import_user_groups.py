"""Import user groups

Revision ID: 7fa4d0b48662
Revises: 0143c6e15141
Create Date: 2020-10-28 08:33:12.741038

"""

# revision identifiers, used by Alembic.
revision = "7fa4d0b48662"
down_revision = "d87c53d0e1d4"
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.create_table(
        "usergroupimport",
        sa.Column("usergroup_id", sa.Integer(), nullable=False),
        sa.Column("usergroupimport_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(
            ["usergroup_id"],
            ["usergroup.id"],
            name=op.f("fk_usergroupimport_usergroup_id_usergroup"),
        ),
        sa.ForeignKeyConstraint(
            ["usergroupimport_id"],
            ["usergroup.id"],
            name=op.f("fk_usergroupimport_usergroupimport_id_usergroup"),
        ),
        sa.UniqueConstraint(
            "usergroup_id", "usergroupimport_id", name=op.f("uq_usergroupimport_usergroup_id")
        ),
    )


def downgrade():
    op.drop_table("usergroupimport")
