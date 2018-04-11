"""Add interpretation workflow_status

Revision ID: 82e7b7ca0ab8
Revises: 8272b3675971
Create Date: 2018-04-10 10:36:43.810548

"""

# revision identifiers, used by Alembic.
revision = '82e7b7ca0ab8'
down_revision = '8272b3675971'
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa
from sqlalchemy.sql import table, column
from sqlalchemy.dialects import postgresql


AlleleInterpretation = table(
    'alleleinterpretation',
    column('id', sa.Integer),
    column('allele_id', sa.Integer),
    column('end_action', sa.String()),
    column('workflow_status', sa.String()),
    column('date_last_update', sa.DateTime()),
    column('finalized', sa.Boolean),
)


AnalysisInterpretation = table(
    'analysisinterpretation',
    column('id', sa.Integer),
    column('analysis_id', sa.Integer),
    column('end_action', sa.String()),
    column('workflow_status', sa.String()),
    column('date_last_update', sa.DateTime()),
    column('finalized', sa.Boolean),
)


def migrate_interpretations(conn, model, id_attr):
    ids = conn.execute(
        sa.select([getattr(model.c, id_attr)]).distinct()
    )
    for obj_id in ids:
        obj_id = obj_id[0]
        interpretations = conn.execute(
            sa.select(
                [
                    model.c.id,
                    model.c.end_action
                ]
            ).where(getattr(model.c, id_attr) == obj_id).order_by(model.c.date_last_update)
        )

        for idx, i in enumerate(interpretations):

            values = {
                # In old format, any round (except first) is a review
                'workflow_status': 'Classification' if idx == 0 else 'Review'
            }

            if i.end_action == 'Finalize':
                values['finalized'] = True
            conn.execute(
                sa.update(model).where(
                    model.c.id == i.id
                ).values(**values)
            )


def upgrade():

    conn = op.get_bind()

    workflow_status = sa.Enum('Not ready', 'Classification', 'Review', 'Medical review', name='interpretation_workflow_status')
    workflow_status.create(conn, checkfirst=True)

    # AlleleInterpretation
    op.add_column('alleleinterpretation', sa.Column('finalized', sa.Boolean(), nullable=True))
    op.add_column('alleleinterpretation', sa.Column('workflow_status', workflow_status, nullable=True))

    migrate_interpretations(conn, AlleleInterpretation, 'allele_id')

    op.alter_column('alleleinterpretation', 'workflow_status', nullable=False)
    op.drop_column('alleleinterpretation', 'end_action')

    # AnalysisInterpretation
    op.add_column('analysisinterpretation', sa.Column('finalized', sa.Boolean(), nullable=True))
    op.add_column('analysisinterpretation', sa.Column('workflow_status', workflow_status, nullable=True))

    migrate_interpretations(conn, AnalysisInterpretation, 'analysis_id')
    op.alter_column('analysisinterpretation', 'workflow_status', nullable=False)
    op.drop_column('analysisinterpretation', 'end_action')


def downgrade():
    raise NotImplementedError("Downgrade not possible!")
