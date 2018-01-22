"""New analysis and annotationjob columns

Revision ID: 551da543894c
Revises: ebcfe9e6a769
Create Date: 2018-01-22 08:38:45.571134

"""

# revision identifiers, used by Alembic.
revision = '551da543894c'
down_revision = 'ebcfe9e6a769'
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.add_column('analysis', sa.Column('report', sa.String(), nullable=True))
    op.add_column('analysis', sa.Column('warnings', sa.String(), nullable=True))
    # Remove all current jobs
    op.execute('DELETE FROM annotationjob')
    op.add_column('annotationjob', sa.Column('data', sa.String(), nullable=False))
    op.drop_column('annotationjob', 'vcf')
    op.add_column('usergroup', sa.Column('default_import_genepanel_name', sa.String(), nullable=True))
    op.add_column('usergroup', sa.Column('default_import_genepanel_version', sa.String(), nullable=True))
    op.create_foreign_key(op.f('fk_usergroup_default_import_genepanel_name_genepanel'), 'usergroup', 'genepanel', ['default_import_genepanel_name', 'default_import_genepanel_version'], ['name', 'version'])


def downgrade():
    op.drop_constraint(op.f('fk_usergroup_default_import_genepanel_name_genepanel'), 'usergroup', type_='foreignkey')
    op.drop_column('usergroup', 'default_import_genepanel_version')
    op.drop_column('usergroup', 'default_import_genepanel_name')
    op.add_column('annotationjob', sa.Column('vcf', sa.VARCHAR(), autoincrement=False, nullable=False))
    op.drop_column('annotationjob', 'data')
    op.drop_column('analysis', 'warnings')
    op.drop_column('analysis', 'report')
