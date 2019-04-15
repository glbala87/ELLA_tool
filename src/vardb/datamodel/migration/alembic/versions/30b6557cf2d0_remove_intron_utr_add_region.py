"""remove-intron-utr-add-region

Revision ID: 30b6557cf2d0
Revises: 3aa5e573699c
Create Date: 2018-06-04 09:02:04.012457

"""

# revision identifiers, used by Alembic.
revision = "30b6557cf2d0"
down_revision = "3aa5e573699c"
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# Doing migrations as suggested in https://stackoverflow.com/a/14845740

old_options = ("FREQUENCY", "UTR", "GENE", "INTRON")
tmp_options = ("FREQUENCY", "UTR", "GENE", "INTRON", "REGION")
new_options = ("FREQUENCY", "REGION", "GENE")

old_type = sa.Enum(*old_options, name="interpretationsnapshot_filtered")
tmp_type = sa.Enum(*tmp_options, name="tmp_interpretation_snapshot_filtered")
new_type = sa.Enum(*new_options, name="interpretationsnapshot_filtered")

analysisinterpretationsnapshot = sa.sql.table(
    "analysisinterpretationsnapshot",
    sa.Column("interpretationsnapshot_filtered", new_type, nullable=True),
)
alleleinterpretationsnapshot = sa.sql.table(
    "analysisinterpretationsnapshot",
    sa.Column("interpretationsnapshot_filtered", new_type, nullable=True),
)


def upgrade():
    # Create a temporary "tmp_interpretation_snapshot_filtered" type, convert and drop the "old" type
    tmp_type.create(op.get_bind(), checkfirst=False)
    op.execute(
        "ALTER TABLE analysisinterpretationsnapshot ALTER COLUMN filtered TYPE tmp_interpretation_snapshot_filtered"
        " USING filtered::text::tmp_interpretation_snapshot_filtered"
    )
    op.execute(
        "ALTER TABLE alleleinterpretationsnapshot ALTER COLUMN filtered TYPE tmp_interpretation_snapshot_filtered"
        " USING filtered::text::tmp_interpretation_snapshot_filtered"
    )
    old_type.drop(op.get_bind(), checkfirst=False)

    # Update values to match new ENUM
    op.execute(
        "UPDATE analysisinterpretationsnapshot SET filtered='REGION' where filtered='UTR' or filtered='INTRON'"
    )

    # Create and convert to the "new" interpretationsnapshot_filtered type
    new_type.create(op.get_bind(), checkfirst=False)
    op.execute(
        "ALTER TABLE analysisinterpretationsnapshot ALTER COLUMN filtered TYPE interpretationsnapshot_filtered"
        " USING filtered::text::interpretationsnapshot_filtered"
    )
    op.execute(
        "ALTER TABLE alleleinterpretationsnapshot ALTER COLUMN filtered TYPE interpretationsnapshot_filtered"
        " USING filtered::text::interpretationsnapshot_filtered"
    )
    tmp_type.drop(op.get_bind(), checkfirst=False)


def downgrade():
    raise NotImplementedError("Downgrade not possible")
