"""Broadcast

Revision ID: 61b990b84ed2
Revises: bbe1686834a4
Create Date: 2018-09-28 14:46:50.660436

"""

# revision identifiers, used by Alembic.
revision = '61b990b84ed2'
down_revision = 'bbe1686834a4'
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa


def upgrade():

    op.create_table(
        'broadcast',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('date_created', sa.DateTime(timezone=True), nullable=False),
        sa.Column('message', sa.String(), nullable=False),
        sa.Column('active', sa.Boolean(), nullable=False),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_broadcast'))
    )


def downgrade():
    op.drop_table('broadcast')
