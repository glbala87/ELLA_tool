"""Remove referenceassessments from resused alleleassessments

Revision ID: d6290a3fdf7b
Revises: 4dee968751a0
Create Date: 2019-10-30 14:45:38.395240

"""

# revision identifiers, used by Alembic.
revision = "d6290a3fdf7b"
down_revision = "4dee968751a0"
branch_labels = None
depends_on = None

import logging
from alembic import op
import sqlalchemy as sa

from sqlalchemy.sql import column, table
from vardb.util.mutjson import JSONMutableDict
from sqlalchemy.dialects.postgresql import JSONB

log = logging.getLogger(__name__)

AnalysisInterpretation = table(
    "analysisinterpretation",
    column("id", sa.Integer()),
    column("state", JSONMutableDict.as_mutable(JSONB)),
)


AlleleInterpretation = table(
    "alleleinterpretation",
    column("id", sa.Integer()),
    column("state", JSONMutableDict.as_mutable(JSONB)),
)


def upgrade():
    conn = op.get_bind()
    for model in [AnalysisInterpretation, AlleleInterpretation]:
        res = conn.execute(sa.select([model.c.id, model.c.state]))
        for row in res:
            for allele_id, allele_state in row.state.get("allele", {}).items():
                # If allele assessment not reused, skip
                if not allele_state["alleleassessment"].get("reuse", False):
                    continue

                referenceassessments = allele_state["referenceassessments"]
                # We know this is only caused by referenceassessments autoignore according to user group config, and if they have evaluation, they are not reused
                new_referenceassessments = [
                    ra
                    for ra in referenceassessments
                    if ra.get("evaluation", {}).get("comment", "")
                    != "Automatically ignored according to user group configuration"
                ]

                # Skip if not any change to referenceassessments
                if new_referenceassessments == referenceassessments:
                    continue

                new_state = dict(row.state)
                new_state["allele"][allele_id]["referenceassessments"] = new_referenceassessments

                log.debug(
                    "Updating {} {} (from {} to {} referenceassessments)".format(
                        model.name, row.id, len(referenceassessments), len(new_referenceassessments)
                    )
                )
                conn.execute(sa.update(model).where(model.c.id == row.id).values(state=new_state))


def downgrade():
    raise NotImplementedError("Downgrade not supported")
