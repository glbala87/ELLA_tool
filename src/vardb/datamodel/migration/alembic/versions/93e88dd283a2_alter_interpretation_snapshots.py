"""Alter interpretation snapshots

Revision ID: 93e88dd283a2
Revises: 16a0a693b537
Create Date: 2019-12-02 09:44:16.636082

"""

# revision identifiers, used by Alembic.
revision = "93e88dd283a2"
down_revision = "16a0a693b537"
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa


def get_interpretation_alleleassessment_query(interpretationtype: str) -> str:
    assert interpretationtype in ["analysisinterpretation", "alleleinterpretation"]
    return f"""INSERT INTO interpretationlog
        ({interpretationtype}_id, user_id, date_created, alleleassessment_id, allelereport_id)
        SELECT
            ais.{interpretationtype}_id,
            ai.user_id,
            ais.date_created,
            ais.alleleassessment_id,
            CASE WHEN
                ais.allelereport_id != coalesce(ais.presented_allelereport_id, 0)
                THEN ais.allelereport_id ELSE null
            END
        FROM {interpretationtype}snapshot AS ais
        JOIN {interpretationtype} AS ai ON ais.{interpretationtype}_id = ai.id
        WHERE ai.finalized IS true
            AND ais.alleleassessment_id != coalesce(ais.presented_alleleassessment_id, 0)
            AND ais.alleleassessment_id IS NOT NULL
        ORDER BY ais.date_created
    """


def get_interpretation_allelereport_query(interpretationtype: str) -> str:
    assert interpretationtype in ["analysisinterpretation", "alleleinterpretation"]
    return f"""INSERT INTO interpretationlog
        ({interpretationtype}_id, user_id, date_created, alleleassessment_id, allelereport_id)
        SELECT ais.{interpretationtype}_id, ai.user_id, ais.date_created, null, ais.allelereport_id
        FROM {interpretationtype}snapshot AS ais
        JOIN {interpretationtype} AS ai ON ais.{interpretationtype}_id = ai.id
        WHERE ai.finalized IS true
            AND ais.alleleassessment_id = ais.presented_alleleassessment_id
            AND ais.allelereport_id != coalesce(ais.presented_allelereport_id, 0)
            AND ais.allelereport_id IS NOT NULL
        ORDER BY ais.date_created
    """


def upgrade():

    # Change overview:
    # presented_alleleassessment_id and alleleassessment_id in snapshot table
    # indicated before/after id for alleleassessment in finalization of alleles.
    # Since we now finalize alleles outside of the finish workflow step, before
    # and after makes no sense. We thus only store the snapshot of what the user saw upon
    # finalization of the workflow.
    #
    # We migrate the existing before data (i.e alleleassessment_id and allelereport_id) to
    # created alleleassessment/allelereport entries in interpretation log.
    #
    # - presented_alleleassessment_id has been renamed to alleleassessment_id
    # - presented_allelereport_id has been renamed to allelereport_id
    #
    # Also, we've added usergroup_id to assessments/report, so we need to populate that
    # in addition to making user_id on same tables not nullable

    # Add alleleassessment/allelereport to interpretation log
    op.add_column(
        "interpretationlog", sa.Column("alleleassessment_id", sa.Integer(), nullable=True)
    )
    op.create_foreign_key(
        op.f("fk_interpretationlog_alleleassessment_id_alleleassessment"),
        "interpretationlog",
        "alleleassessment",
        ["alleleassessment_id"],
        ["id"],
    )
    op.add_column("interpretationlog", sa.Column("allelereport_id", sa.Integer(), nullable=True))
    op.create_foreign_key(
        op.f("fk_interpretationlog_allelereport_id_allelereport"),
        "interpretationlog",
        "allelereport",
        ["allelereport_id"],
        ["id"],
    )

    # Migrate data from interpretation snapshot tables to interpretation log
    # There are two cases for each, one where alleleassessment and allelereport are both created
    # at the same time. This is the usual case
    # Other case is when only allelereport was created, but not alleleassessment. This happens
    # when user updated variant report only.

    # Analysisinterpretation
    op.execute(get_interpretation_alleleassessment_query("analysisinterpretation"))
    op.execute(get_interpretation_allelereport_query("analysisinterpretation"))

    # Alleleinterpretation
    op.execute(get_interpretation_alleleassessment_query("alleleinterpretation"))
    op.execute(get_interpretation_allelereport_query("alleleinterpretation"))

    # Drop migrated columns
    op.drop_constraint(
        "fk_analysisinterpretationsnapshot_allelereport_id_allelereport",
        "analysisinterpretationsnapshot",
        type_="foreignkey",
    )
    op.drop_constraint(
        "fk_analysisinterpretationsnapshot_alleleassessment_id_alleleass",
        "analysisinterpretationsnapshot",
        type_="foreignkey",
    )
    op.drop_column("analysisinterpretationsnapshot", "alleleassessment_id")
    op.drop_column("analysisinterpretationsnapshot", "allelereport_id")
    op.drop_constraint(
        "fk_alleleinterpretationsnapshot_allelereport_id_allelereport",
        "alleleinterpretationsnapshot",
        type_="foreignkey",
    )
    op.drop_constraint(
        "fk_alleleinterpretationsnapshot_alleleassessment_id_alleleasses",
        "alleleinterpretationsnapshot",
        type_="foreignkey",
    )
    op.drop_column("alleleinterpretationsnapshot", "alleleassessment_id")
    op.drop_column("alleleinterpretationsnapshot", "allelereport_id")

    # Rename columns presented_*_id -> *_id
    # We cannot rename constraints, so drop and recreate the foreign keys..
    op.alter_column(
        "analysisinterpretationsnapshot",
        "presented_alleleassessment_id",
        new_column_name="alleleassessment_id",
    )
    op.alter_column(
        "analysisinterpretationsnapshot",
        "presented_allelereport_id",
        new_column_name="allelereport_id",
    )

    op.alter_column(
        "alleleinterpretationsnapshot",
        "presented_alleleassessment_id",
        new_column_name="alleleassessment_id",
    )
    op.alter_column(
        "alleleinterpretationsnapshot",
        "presented_allelereport_id",
        new_column_name="allelereport_id",
    )

    op.drop_constraint(
        "fk_alleleinterpretationsnapshot_presented_alleleassessment_id_a",
        "alleleinterpretationsnapshot",
        type_="foreignkey",
    )
    op.drop_constraint(
        "fk_alleleinterpretationsnapshot_presented_allelereport_id_allel",
        "alleleinterpretationsnapshot",
        type_="foreignkey",
    )
    op.drop_constraint(
        "fk_analysisinterpretationsnapshot_presented_allelereport_id_all",
        "analysisinterpretationsnapshot",
        type_="foreignkey",
    )
    op.drop_constraint(
        "fk_analysisinterpretationsnapshot_presented_alleleassessment_id",
        "analysisinterpretationsnapshot",
        type_="foreignkey",
    )

    op.create_foreign_key(
        "fk_analysisinterpretationsnapshot_allelereport_id_allelereport",
        "analysisinterpretationsnapshot",
        "allelereport",
        ["allelereport_id"],
        ["id"],
    )

    op.create_foreign_key(
        "fk_analysisinterpretationsnapshot_alleleassessment_id_alleleass",
        "analysisinterpretationsnapshot",
        "alleleassessment",
        ["alleleassessment_id"],
        ["id"],
    )
    op.create_foreign_key(
        "fk_alleleinterpretationsnapshot_allelereport_id_allelereport",
        "alleleinterpretationsnapshot",
        "allelereport",
        ["allelereport_id"],
        ["id"],
    )
    op.create_foreign_key(
        "fk_alleleinterpretationsnapshot_alleleassessment_id_alleleasses",
        "alleleinterpretationsnapshot",
        "alleleassessment",
        ["alleleassessment_id"],
        ["id"],
    )

    # End rename columns

    # Populate usergroup_id
    op.add_column("alleleassessment", sa.Column("usergroup_id", sa.Integer(), nullable=True))
    op.create_foreign_key(
        op.f("fk_alleleassessment_usergroup_id_usergroup"),
        "alleleassessment",
        "usergroup",
        ["usergroup_id"],
        ["id"],
    )

    op.add_column("allelereport", sa.Column("usergroup_id", sa.Integer(), nullable=True))
    op.create_foreign_key(
        op.f("fk_allelereport_usergroup_id_usergroup"),
        "allelereport",
        "usergroup",
        ["usergroup_id"],
        ["id"],
    )

    op.add_column("referenceassessment", sa.Column("usergroup_id", sa.Integer(), nullable=True))
    op.create_foreign_key(
        op.f("fk_referenceassessment_usergroup_id_usergroup"),
        "referenceassessment",
        "usergroup",
        ["usergroup_id"],
        ["id"],
    )

    op.execute(
        'UPDATE alleleassessment SET usergroup_id = "user".group_id FROM "user" WHERE "user".id = alleleassessment.user_id'
    )
    op.execute(
        'UPDATE allelereport SET usergroup_id = "user".group_id FROM "user" WHERE "user".id = allelereport.user_id'
    )
    op.execute(
        'UPDATE referenceassessment SET usergroup_id = "user".group_id FROM "user" WHERE "user".id = referenceassessment.user_id'
    )

    # Make user_id not nullable
    op.alter_column("alleleassessment", "user_id", nullable=False)
    op.alter_column("referenceassessment", "user_id", nullable=False)
    op.alter_column("allelereport", "user_id", nullable=False)


def downgrade():
    raise NotImplementedError("Downgrade not possible")
