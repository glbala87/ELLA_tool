"""Interpretation log

Revision ID: bbe1686834a4
Revises: f93cbfcb7ca9
Create Date: 2018-09-07 07:21:47.244333

"""

# revision identifiers, used by Alembic.
revision = 'bbe1686834a4'
down_revision = 'f93cbfcb7ca9'
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.create_table(
        'interpretationlog',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('alleleinterpretation_id', sa.Integer(), nullable=True),
        sa.Column('analysisinterpretation_id', sa.Integer(), nullable=True),
        sa.Column('user_id', sa.Integer(), nullable=True),
        sa.Column('date_created', sa.DateTime(timezone=True), nullable=False),
        sa.Column('message', sa.String(), nullable=True),
        sa.Column('priority', sa.Integer(), nullable=True),
        sa.Column('review_comment', sa.String(), nullable=True),
        sa.Column('warning_cleared', sa.Boolean(), nullable=True),
        sa.ForeignKeyConstraint(['alleleinterpretation_id'], ['alleleinterpretation.id'], name=op.f('fk_interpretationlog_alleleinterpretation_id_alleleinterpretation')),
        sa.ForeignKeyConstraint(['analysisinterpretation_id'], ['analysisinterpretation.id'], name=op.f('fk_interpretationlog_analysisinterpretation_id_analysisinterpretation')),
        sa.ForeignKeyConstraint(['user_id'], ['user.id'], name=op.f('fk_interpretationlog_user_id_user')),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_interpretationlog'))
    )

    # Migrate review comments
    conn = op.get_bind()
    TEMPLATE = """
    SELECT id, user_id, state->'review_comment', date_last_update FROM {table} WHERE
        state->'review_comment' IS NOT null AND status = 'Done' ORDER BY date_last_update;
    """
    al_review_comments = conn.execute(TEMPLATE.format(table='alleleinterpretation'))
    for al_review_comment in al_review_comments:
        conn.execute("INSERT INTO interpretationlog (alleleinterpretation_id, user_id, review_comment, date_created) VALUES ({}, {}, '{}', '{}')".format(*al_review_comment))

    an_review_comments = conn.execute(TEMPLATE.format(table='analysisinterpretation'))
    for an_review_comment in an_review_comments:
        conn.execute("INSERT INTO interpretationlog (analysisinterpretation_id, user_id, review_comment, date_created) VALUES ({}, {}, '{}', '{}')".format(*an_review_comment))

    conn.execute("UPDATE alleleinterpretation SET state = state - 'review_comment'")
    conn.execute("UPDATE analysisinterpretation SET state = state - 'review_comment'")

    # Priority hasn't been used so far, no need to migrate data
    op.drop_column(u'analysis', 'priority')


def downgrade():
    raise NotImplementedError("Downgrade not supported")
