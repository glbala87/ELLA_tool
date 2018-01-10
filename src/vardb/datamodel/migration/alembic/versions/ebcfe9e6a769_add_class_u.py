"""Add class U

Revision ID: ebcfe9e6a769
Revises:
Create Date: 2018-01-03 13:27:54.637294

"""

# revision identifiers, used by Alembic.
revision = 'ebcfe9e6a769'
down_revision = None
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa


new_enum = sa.Enum('1', '2', '3', '4', '5', 'T', 'U', name="alleleassessment_classification")

def upgrade():
    # New model has removed 'native_enum=False'. It was added so we could add new
    # classifications without migrations, but for safety we want to use a proper ENUM after all.
    # We didn't realize 'native_enum=False' created a check constraint behind the scenes anyway,
    # so we need to remove that.
    op.execute("ALTER TABLE alleleassessment DROP CONSTRAINT alleleassessment_classification_check")

    new_enum.create(op.get_bind())
    # Now alter table column to use ENUM instead of VARCHAR
    op.execute("ALTER TABLE alleleassessment ALTER COLUMN classification TYPE alleleassessment_classification USING classification::alleleassessment_classification")


def downgrade():
    raise RuntimeError("Downgrading is not implemented.")
