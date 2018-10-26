"""Filter config

Revision ID: d099628590c9
Revises: 7fddcdb9e856
Create Date: 2018-10-18 08:17:21.321913

"""
import logging

# revision identifiers, used by Alembic.
revision = 'd099628590c9'
down_revision = '7fddcdb9e856'
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

def upgrade():

    op.create_table('filterconfig',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('filterconfig', postgresql.JSONB(), nullable=False),
        sa.Column('usergroup_id', sa.Integer(), nullable=False),
        sa.Column('default', sa.Boolean(), nullable=False),
        sa.ForeignKeyConstraint(['usergroup_id'], ['usergroup.id'], name=op.f('fk_filterconfig_usergroup_id_usergroup')),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_filterconfig')),
        sa.UniqueConstraint('name', name=op.f('uq_filterconfig_name'))
    )

    # Genepanel configs in production are all equal,
    # and will be moved outside to the usergroup config fixture
    # We can therefore drop whole column
    op.drop_column(u'genepanel', 'config')
    logging.warning('!!! WARNING !!!')
    logging.warning('!!! Genepanel config dropped! Remember to migrate the config to usergroup config !!!')


def downgrade():
    raise NotImplementedError("Downgrade not possible")
