"""Interpretation state changes

Revision ID: 662204b12d07
Revises: 4629b478b291
Create Date: 2018-11-08 12:23:44.840307

"""

# revision identifiers, used by Alembic.
revision = '662204b12d07'
down_revision = '4629b478b291'
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB


AlleleInterpretation = sa.table(
    'alleleinterpretation',
    sa.column('id', sa.Integer),
    sa.column('state', JSONB)
)

AnalysisInterpretation = sa.table(
    'analysisinterpretation',
    sa.column('id', sa.Integer),
    sa.column('state', JSONB)
)


def upgrade():

    conn = op.get_bind()

    def update_interpretation_state(model):
        interpretations = conn.execute(sa.select([c for c in model.c]))
        for i_id, state in interpretations:
            state = dict(state)
            if 'allele' in state:
                for allele_id in state['allele']:
                    if 'quality' in state['allele'][allele_id]:
                        state['allele'][allele_id]['analysis'] = state['allele'][allele_id]['quality']
                        del state['allele'][allele_id]['quality']

            conn.execute(model.update().where(model.c.id == i_id).values(
                state=state
            ))

    update_interpretation_state(AlleleInterpretation)
    update_interpretation_state(AnalysisInterpretation)


def downgrade():
    raise NotImplementedError("Downgrade not possible!")
