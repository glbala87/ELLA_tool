"""Interpretation ondelete rules

Revision ID: 0143c6e15141
Revises: 61779f00886c
Create Date: 2020-08-10 09:57:11.167758

"""

# revision identifiers, used by Alembic.
revision = "0143c6e15141"
down_revision = "61779f00886c"
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.drop_constraint(
        "fk_alleleassessment_analysis_id_analysis", "alleleassessment", type_="foreignkey"
    )
    op.create_foreign_key(
        op.f("fk_alleleassessment_analysis_id_analysis"),
        "alleleassessment",
        "analysis",
        ["analysis_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.drop_constraint(
        "fk_alleleinterpretationsnapshot_alleleinterpretation_id_allelei",
        "alleleinterpretationsnapshot",
        type_="foreignkey",
    )
    op.create_foreign_key(
        op.f("fk_alleleinterpretationsnapshot_alleleinterpretation_id_alleleinterpretation"),
        "alleleinterpretationsnapshot",
        "alleleinterpretation",
        ["alleleinterpretation_id"],
        ["id"],
        ondelete="CASCADE",
    )
    op.drop_constraint("fk_allelereport_analysis_id_analysis", "allelereport", type_="foreignkey")
    op.create_foreign_key(
        op.f("fk_allelereport_analysis_id_analysis"),
        "allelereport",
        "analysis",
        ["analysis_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.drop_constraint(
        "fk_geneassessment_analysis_id_analysis", "geneassessment", type_="foreignkey"
    )
    op.create_foreign_key(
        op.f("fk_geneassessment_analysis_id_analysis"),
        "geneassessment",
        "analysis",
        ["analysis_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.drop_constraint(
        "fk_interpretationlog_alleleinterpretation_id_alleleinterpretati",
        "interpretationlog",
        type_="foreignkey",
    )
    op.create_foreign_key(
        op.f("fk_interpretationlog_alleleinterpretation_id_alleleinterpretation"),
        "interpretationlog",
        "alleleinterpretation",
        ["alleleinterpretation_id"],
        ["id"],
        ondelete="CASCADE",
    )
    op.drop_constraint(
        "fk_interpretationstatehistory_alleleinterpretation_id_alleleint",
        "interpretationstatehistory",
        type_="foreignkey",
    )
    op.create_foreign_key(
        op.f("fk_interpretationstatehistory_alleleinterpretation_id_alleleinterpretation"),
        "interpretationstatehistory",
        "alleleinterpretation",
        ["alleleinterpretation_id"],
        ["id"],
        ondelete="CASCADE",
    )
    op.drop_constraint(
        "fk_referenceassessment_analysis_id_analysis", "referenceassessment", type_="foreignkey"
    )
    op.create_foreign_key(
        op.f("fk_referenceassessment_analysis_id_analysis"),
        "referenceassessment",
        "analysis",
        ["analysis_id"],
        ["id"],
        ondelete="SET NULL",
    )


def downgrade():
    op.drop_constraint(
        op.f("fk_referenceassessment_analysis_id_analysis"),
        "referenceassessment",
        type_="foreignkey",
    )
    op.create_foreign_key(
        "fk_referenceassessment_analysis_id_analysis",
        "referenceassessment",
        "analysis",
        ["analysis_id"],
        ["id"],
    )
    op.drop_constraint(
        op.f("fk_interpretationstatehistory_alleleinterpretation_id_alleleinterpretation"),
        "interpretationstatehistory",
        type_="foreignkey",
    )
    op.create_foreign_key(
        "fk_interpretationstatehistory_alleleinterpretation_id_alleleint",
        "interpretationstatehistory",
        "alleleinterpretation",
        ["alleleinterpretation_id"],
        ["id"],
    )
    op.drop_constraint(
        op.f("fk_interpretationlog_alleleinterpretation_id_alleleinterpretation"),
        "interpretationlog",
        type_="foreignkey",
    )
    op.create_foreign_key(
        "fk_interpretationlog_alleleinterpretation_id_alleleinterpretati",
        "interpretationlog",
        "alleleinterpretation",
        ["alleleinterpretation_id"],
        ["id"],
    )
    op.drop_constraint(
        op.f("fk_geneassessment_analysis_id_analysis"), "geneassessment", type_="foreignkey"
    )
    op.create_foreign_key(
        "fk_geneassessment_analysis_id_analysis",
        "geneassessment",
        "analysis",
        ["analysis_id"],
        ["id"],
    )
    op.drop_constraint(
        op.f("fk_allelereport_analysis_id_analysis"), "allelereport", type_="foreignkey"
    )
    op.create_foreign_key(
        "fk_allelereport_analysis_id_analysis", "allelereport", "analysis", ["analysis_id"], ["id"]
    )
    op.drop_constraint(
        op.f("fk_alleleinterpretationsnapshot_alleleinterpretation_id_alleleinterpretation"),
        "alleleinterpretationsnapshot",
        type_="foreignkey",
    )
    op.create_foreign_key(
        "fk_alleleinterpretationsnapshot_alleleinterpretation_id_allelei",
        "alleleinterpretationsnapshot",
        "alleleinterpretation",
        ["alleleinterpretation_id"],
        ["id"],
    )
    op.drop_constraint(
        op.f("fk_alleleassessment_analysis_id_analysis"), "alleleassessment", type_="foreignkey"
    )
    op.create_foreign_key(
        "fk_alleleassessment_analysis_id_analysis",
        "alleleassessment",
        "analysis",
        ["analysis_id"],
        ["id"],
    )
