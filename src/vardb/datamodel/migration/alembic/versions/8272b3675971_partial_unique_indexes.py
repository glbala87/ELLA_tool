"""Partial unique indexes

Revision ID: 8272b3675971
Revises: 
Create Date: 2018-03-05 11:37:55.996201

"""

# revision identifiers, used by Alembic.
revision = '8272b3675971'
down_revision = None
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa


def upgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.create_index('ix_assessment_alleleid_unique', 'alleleassessment', ['allele_id'], unique=True, postgresql_where=sa.text(u'date_superceeded IS NULL'))
    op.create_index('ix_alleleinterpretation_alleleid_ongoing_unique', 'alleleinterpretation', ['allele_id'], unique=True, postgresql_where=sa.text(u"status IN ('Ongoing', 'Not started')"))
    op.create_index('ix_allelereport_alleleid_unique', 'allelereport', ['allele_id'], unique=True, postgresql_where=sa.text(u'date_superceeded IS NULL'))
    op.create_index('ix_analysisinterpretation_analysisid_ongoing_unique', 'analysisinterpretation', ['analysis_id'], unique=True, postgresql_where=sa.text(u"status IN ('Ongoing', 'Not started')"))
    op.create_index('ix_annotation_unique', 'annotation', ['allele_id'], unique=True, postgresql_where=sa.text(u'date_superceeded IS NULL'))
    op.create_index('ix_customannotation_unique', 'customannotation', ['allele_id'], unique=True, postgresql_where=sa.text(u'date_superceeded IS NULL'))
    op.create_index('ix_referenceassessment_alleleid_referenceid_unique', 'referenceassessment', ['allele_id', 'reference_id'], unique=True, postgresql_where=sa.text(u'date_superceeded IS NULL'))
    ### end Alembic commands ###


def downgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.drop_index('ix_referenceassessment_alleleid_referenceid_unique', table_name='referenceassessment')
    op.drop_index('ix_customannotation_unique', table_name='customannotation')
    op.drop_index('ix_annotation_unique', table_name='annotation')
    op.drop_index('ix_analysisinterpretation_analysisid_ongoing_unique', table_name='analysisinterpretation')
    op.drop_index('ix_allelereport_alleleid_unique', table_name='allelereport')
    op.drop_index('ix_alleleinterpretation_alleleid_ongoing_unique', table_name='alleleinterpretation')
    op.drop_index('ix_assessment_alleleid_unique', table_name='alleleassessment')
    ### end Alembic commands ###