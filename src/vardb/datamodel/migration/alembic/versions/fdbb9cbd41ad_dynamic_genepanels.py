"""Dynamic genepanels

Revision ID: fdbb9cbd41ad
Revises: 82e7b7ca0ab8
Create Date: 2018-05-04 08:45:01.517644

"""

# revision identifiers, used by Alembic.
revision = 'fdbb9cbd41ad'
down_revision = '82e7b7ca0ab8'
branch_labels = None
depends_on = None

from collections import defaultdict
from alembic import op
import sqlalchemy as sa

from sqlalchemy.sql import table, column
from sqlalchemy.dialects import postgresql


Phenotype = table(
    'phenotype',
    column('id', sa.Integer),
    column('gene_id', sa.Integer),
    column('description', sa.String()),
    column('inheritance', sa.String()),
    column('genepanel_name', sa.String()),
    column('genepanel_version', sa.String()),
)


def upgrade():
    conn = op.get_bind()

    # Annotationjob
    op.add_column(u'annotationjob', sa.Column('sample_id', sa.String(), nullable=True))
    op.alter_column(
        u'annotationjob',
        'data',
        existing_type=sa.VARCHAR(),
        nullable=True
    )

    ## Genepanel
    op.add_column(u'genepanel', sa.Column('official', sa.Boolean()))
    op.execute('UPDATE genepanel SET official = true')
    op.alter_column('genepanel', 'official', nullable=False)

    op.add_column(u'genepanel', sa.Column('date_created', sa.DateTime(timezone=True)))
    op.execute('UPDATE genepanel SET date_created = current_timestamp')
    op.alter_column('genepanel', 'date_created', nullable=False)

    op.add_column(u'genepanel', sa.Column('user_id', sa.Integer(), nullable=True))

    # Migrate phenotypes
    op.drop_column(u'phenotype', 'comment')
    op.drop_column(u'phenotype', 'pmid')
    op.drop_column(u'phenotype', 'inheritance_info')

    op.create_table('genepanel_phenotype',
        sa.Column('genepanel_name', sa.String(), nullable=False),
        sa.Column('genepanel_version', sa.String(), nullable=False),
        sa.Column('phenotype_id', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(
            ['genepanel_name', 'genepanel_version'],
            ['genepanel.name', 'genepanel.version'],
            name=op.f('fk_genepanel_phenotype_genepanel_name_genepanel'),
            ondelete='CASCADE'
        ),
        sa.ForeignKeyConstraint(
            ['phenotype_id'],
            ['phenotype.id'],
            name=op.f('fk_genepanel_phenotype_phenotype_id_phenotype')
        )
    )

    phenotypes = conn.execute(
        sa.select(
            [
                Phenotype.c.id,
                Phenotype.c.gene_id,
                Phenotype.c.description,
                Phenotype.c.inheritance,
                Phenotype.c.genepanel_name,
                Phenotype.c.genepanel_version
            ]
        )
    )

    # Delete redundant phenotypes and connect the rest to genepanel via genepanel_phenotype table
    ordered_phenotypes = defaultdict(list)
    for p in phenotypes:
        p_key = (p.gene_id, p.description, p.inheritance)
        ordered_phenotypes[p_key].append(p)

    for phenotypes in ordered_phenotypes.values():

        # Get genepanels that should connect to this phenotype
        genepanels = [(p['genepanel_name'], p['genepanel_version']) for p in phenotypes]

        # Keep first in database, delete the rest
        p = phenotypes.pop(0)
        for p_delete in phenotypes:
            conn.execute('DELETE FROM phenotype WHERE id = {}'.format(p_delete.id))

        # Connect phenotype to genepanels via new table
        for genepanel in genepanels:
            phenotypes = conn.execute(
                'INSERT INTO genepanel_phenotype (phenotype_id, genepanel_name, genepanel_version) VALUES ({}, \'{}\', \'{}\')'.format(p.id, genepanel[0], genepanel[1])
            )

    op.create_foreign_key(op.f('fk_genepanel_user_id_user'), 'genepanel', 'user', ['user_id'], ['id'])
    op.create_unique_constraint(op.f('uq_phenotype_gene_id'), 'phenotype', ['gene_id', 'description', 'inheritance'])

    op.drop_constraint(u'fk_phenotype_genepanel_name_genepanel', 'phenotype', type_='foreignkey')
    op.drop_column(u'phenotype', 'genepanel_name')
    op.drop_column(u'phenotype', 'genepanel_version')


def downgrade():
    raise NotImplementedError('Downgrade not possible')
