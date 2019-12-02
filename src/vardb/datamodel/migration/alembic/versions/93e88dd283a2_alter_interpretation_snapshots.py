"""Alter interpretation snapshots

Revision ID: 93e88dd283a2
Revises: d6290a3fdf7b
Create Date: 2019-12-02 09:44:16.636082

"""

# revision identifiers, used by Alembic.
revision = "93e88dd283a2"
down_revision = "d6290a3fdf7b"
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa


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
    # - The existing alleleassessment_id and allelereport_id fields indicated ,
    #

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
    op.execute(
        f"""INSERT INTO interpretationlog
        (analysisinterpretation_id, user_id, date_created, alleleassessment_id, allelereport_id)
        SELECT
            ais.analysisinterpretation_id,
            ai.user_id,
            ais.date_created,
            ais.alleleassessment_id,
            CASE WHEN
                ais.allelereport_id != coalesce(ais.presented_allelereport_id, 0)
                THEN ais.allelereport_id ELSE null
            END
        FROM analysisinterpretationsnapshot AS ais
        JOIN analysisinterpretation AS ai ON ais.analysisinterpretation_id = ai.id
        WHERE ai.finalized IS true
            AND ais.alleleassessment_id != coalesce(ais.presented_alleleassessment_id, 0)
            AND ais.alleleassessment_id IS NOT NULL
        ORDER BY ais.date_created
        """
    )

    op.execute(
        f"""INSERT INTO interpretationlog
        (analysisinterpretation_id, user_id, date_created, alleleassessment_id, allelereport_id)
        SELECT ais.analysisinterpretation_id, ai.user_id, ais.date_created, null, ais.allelereport_id
        FROM analysisinterpretationsnapshot AS ais
        JOIN analysisinterpretation AS ai ON ais.analysisinterpretation_id = ai.id
        WHERE ai.finalized IS true
            AND ais.alleleassessment_id = ais.presented_alleleassessment_id
            AND ais.allelereport_id != coalesce(ais.presented_allelereport_id, 0)
            AND ais.allelereport_id IS NOT NULL
        ORDER BY ais.date_created
        """
    )

    # Alleleinterpretation
    op.execute(
        f"""INSERT INTO interpretationlog
        (alleleinterpretation_id, user_id, date_created, alleleassessment_id, allelereport_id)
        SELECT
            ais.alleleinterpretation_id,
            ai.user_id,
            ais.date_created,
            ais.alleleassessment_id,
            CASE WHEN
                ais.allelereport_id != coalesce(ais.presented_allelereport_id, 0)
                THEN ais.allelereport_id ELSE null
            END
        FROM alleleinterpretationsnapshot AS ais
        JOIN alleleinterpretation AS ai ON ais.alleleinterpretation_id = ai.id
        WHERE ai.finalized IS true
            AND ais.alleleassessment_id != coalesce(ais.presented_alleleassessment_id, 0)
            AND ais.alleleassessment_id IS NOT NULL
        ORDER BY ais.date_created
        """
    )

    op.execute(
        f"""INSERT INTO interpretationlog
        (alleleinterpretation_id, user_id, date_created, alleleassessment_id, allelereport_id)
        SELECT ais.alleleinterpretation_id, ai.user_id, ais.date_created, null, ais.allelereport_id
        FROM alleleinterpretationsnapshot AS ais
        JOIN alleleinterpretation AS ai ON ais.alleleinterpretation_id = ai.id
        WHERE ai.finalized IS true
            AND ais.alleleassessment_id = ais.presented_alleleassessment_id
            AND ais.allelereport_id != coalesce(ais.presented_allelereport_id, 0)
            AND ais.allelereport_id IS NOT NULL
        ORDER BY ais.date_created
        """
    )

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


def downgrade():
    raise NotImplementedError("Downgrade not possible")
