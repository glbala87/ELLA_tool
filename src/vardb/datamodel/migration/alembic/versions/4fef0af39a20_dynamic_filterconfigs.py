"""Dynamic filterconfigs

Revision ID: 4fef0af39a20
Revises: 99287295d7fe
Create Date: 2019-01-18 13:48:31.007780

"""

# revision identifiers, used by Alembic.
revision = "4fef0af39a20"
down_revision = "99287295d7fe"
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa

from sqlalchemy.sql import column, table
from sqlalchemy.dialects import postgresql
from sqlalchemy.ext.mutable import MutableDict, Mutable
from sqlalchemy.dialects.postgresql import JSONB

from vardb.util.mutjson import JSONMutableDict

AnalysisInterpretation = table(
    "analysisinterpretation",
    column("id", sa.Integer()),
    column("state", JSONMutableDict.as_mutable(JSONB)),
    column("user_id", sa.Integer()),
    column("status", sa.Enum("Not started", "Ongoing", "Done")),
)

FilterConfig = table(
    "filterconfig",
    column("id", sa.Integer()),
    column("name", sa.String()),
    column("active", sa.Boolean()),
    column("usergroup_id", sa.Integer()),
    column("filterconfig", JSONMutableDict.as_mutable(JSONB)),
)

User = table("user", column("id", sa.Integer()), column("group_id", sa.Integer()))


def upgrade():
    conn = op.get_bind()

    # Set all current filterconfigs as inactive
    op.add_column("filterconfig", sa.Column("active", sa.Boolean(), nullable=False))
    op.add_column(
        "filterconfig", sa.Column("date_superceeded", sa.DateTime(timezone=True), nullable=True)
    )

    op.add_column(
        "filterconfig", sa.Column("previous_filterconfig_id", sa.Integer(), nullable=True)
    )
    op.add_column(
        "filterconfig",
        sa.Column(
            "requirements",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default="[]",
        ),
    )

    op.drop_constraint("uq_filterconfig_name", "filterconfig", type_="unique")
    op.create_index(
        "uq_filterconfig_name_active_unique",
        "filterconfig",
        ["name"],
        unique=True,
        postgresql_where=sa.text("active IS true"),
    )

    op.create_foreign_key(
        op.f("fk_filterconfig_previous_filterconfig_filterconfig"),
        "filterconfig",
        "filterconfig",
        ["previous_filterconfig_id"],
        ["id"],
    )
    op.drop_column("filterconfig", "default")

    UserGroupFilterConfig = op.create_table(
        "usergroupfilterconfig",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("usergroup_id", sa.Integer(), nullable=False),
        sa.Column("filterconfig_id", sa.Integer(), nullable=False),
        sa.Column("order", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(
            ["filterconfig_id"],
            ["filterconfig.id"],
            name=op.f("fk_usergroupfilterconfig_filterconfig_id_filterconfig"),
        ),
        sa.ForeignKeyConstraint(
            ["usergroup_id"],
            ["usergroup.id"],
            name=op.f("fk_usergroupfilterconfig_usergroup_id_usergroup"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_usergroupfilterconfig")),
    )

    op.create_index(
        "uq_usergroupfilterconfig_unique",
        "usergroupfilterconfig",
        ["usergroup_id", "filterconfig_id"],
        unique=True,
    )

    # Update all existing filter configs, rename to 'Legacy' and set as inactive
    # Crete corresponding rows in the UserGroupFilterConfig association table
    conn.execute(sa.update(FilterConfig).values(name="Legacy", active=False))
    existing_filterconfigs = conn.execute(sa.select(FilterConfig.c))
    for fc in existing_filterconfigs:
        conn.execute(
            sa.insert(UserGroupFilterConfig).values(
                usergroup_id=fc.usergroup_id, filterconfig_id=fc.id, order=0
            )
        )

    op.drop_column("filterconfig", "usergroup_id")

    # Set all existing analysis interpretations to point to the legacy filter config for the relevant user group
    analysis_interpretations = conn.execute(
        sa.select(AnalysisInterpretation.c).where(~AnalysisInterpretation.c.user_id.is_(None))
    )
    for ai in analysis_interpretations:
        group_id = conn.execute(sa.select([User.c.group_id]).where(User.c.id == ai.user_id))
        group_id = list(group_id)[0][0]
        fc_id = list(
            conn.execute(
                sa.select([UserGroupFilterConfig.c.filterconfig_id]).where(
                    UserGroupFilterConfig.c.usergroup_id == group_id
                )
            )
        )
        assert len(fc_id) == 1
        fc_id = fc_id[0][0]
        state = ai.state
        state["filterconfigId"] = fc_id
        conn.execute(
            sa.update(AnalysisInterpretation)
            .where(AnalysisInterpretation.c.id == ai.id)
            .values(state=state)
        )

    print("!!! Remember to update filter configs !!!")


def downgrade():
    raise NotImplementedError("Downgrade not possible")
