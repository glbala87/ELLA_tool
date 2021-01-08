"""Redefine classification choices

Revision ID: d87c53d0e1d4
Revises: 0143c6e15141
Create Date: 2020-12-16 14:52:53.513976

"""

# revision identifiers, used by Alembic.
revision = "d87c53d0e1d4"
down_revision = "924438596189"
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB
from vardb.datamodel.migration.utils import update_enum
from sqlalchemy.orm.session import Session
from vardb.datamodel.jsonschemas.update_schemas import update_schemas

OLD_CLASSIFICATIONS = ["1", "2", "3", "4", "5", "U", "DR"]
NEW_CLASSIFICATIONS = ["1", "2", "3", "4", "5", "NP", "DR", "RF"]


def upgrade():
    # Update classification enum
    with update_enum(
        op,
        ["alleleassessment"],
        "classification",
        "alleleassessment_classification",
        OLD_CLASSIFICATIONS,
        NEW_CLASSIFICATIONS,
    ) as tmp_tables:
        conn = op.get_bind()
        # Replace class U with class NP
        conn.execute("UPDATE alleleassessment SET classification='NP' WHERE classification='U'")

    # Update schemas
    session = Session(bind=op.get_bind())
    update_schemas(session)
    session.flush()

    # Update state
    def update_state(state):
        "Replace class U with class NP in state"
        for allele_id in state.get("allele", []):
            if state["allele"][allele_id].get("alleleassessment", {}).get("classification") == "U":
                state["allele"][allele_id]["alleleassessment"]["classification"] = "NP"

    for table_name in [
        "alleleinterpretation",
        "analysisinterpretation",
        "interpretationstatehistory",
    ]:
        tbl = analysisinterpretation = sa.table(
            table_name, sa.column("id", sa.Integer), sa.column("state", JSONB)
        )

        # Work only on states that have classification set to U for one or more alleles
        ids = session.execute(
            f"SELECT DISTINCT id FROM {table_name}, jsonb_each(state->'allele') WHERE (value->'alleleassessment'->'classification')::text='\"U\"'"
        ).fetchall()
        ids = [int(x[0]) for x in ids]

        # Update state row by row
        q = session.query(tbl).filter(tbl.c.id.in_(ids))
        for r in q:
            updated = update_state(r.state)
            session.execute(sa.update(tbl).where(tbl.c.id == r.id).values(state=r.state))
            session.flush()


def downgrade():
    raise NotImplementedError("Downgrade not supported")
