"""text_pattern_ops-indexes

Revision ID: 780575a06f97
Revises: 30b6557cf2d0
Create Date: 2018-06-19 11:44:22.507543

"""

# revision identifiers, used by Alembic.
revision = '780575a06f97'
down_revision = '30b6557cf2d0'
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa


def upgrade():
    print "Creating indexes, this can take a while..."
    op.drop_constraint(u'uq_gene_hgnc_symbol', 'gene', type_='unique')
    op.execute('CREATE UNIQUE INDEX ix_gene_hgnc_symbol ON gene USING btree(lower(hgnc_symbol) text_pattern_ops)')
    op.execute('DROP INDEX IF EXISTS ix_annotationshadowtranscript_hgvsc')
    op.execute('CREATE TABLE IF NOT EXISTS annotationshadowtranscript (hgvsc text)')
    op.execute('CREATE INDEX ix_annotationshadowtranscript_hgvsc ON annotationshadowtranscript USING btree(lower(hgvsc) text_pattern_ops)')


def downgrade():
    raise NotImplementedError("Downgrade not supported")
