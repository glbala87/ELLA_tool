"""Analysis date_requested

Revision ID: da809112fd6c
Revises: 4629b478b291
Create Date: 2018-11-09 11:28:58.160814

"""

revision = 'da809112fd6c'
down_revision = '662204b12d07'
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


def upgrade():
    op.add_column(u'analysis', sa.Column('date_requested', sa.DateTime(timezone=True), nullable=True))
    op.alter_column(u'analysis', 'deposit_date', new_column_name='date_deposited')
    op.alter_column(u'sample', 'deposit_date', new_column_name='date_deposited')


def downgrade():
    op.drop_column(u'analysis', 'date_requested')
    op.alter_column(u'analysis', 'date_deposited', new_column_name='deposit_date')
    op.alter_column(u'sample', 'date_deposited', new_column_name='deposit_date')
