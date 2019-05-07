"""Add analysis cascade delete

Revision ID: 529e8f6faed9
Revises: 12760875ee2d
Create Date: 2019-05-07 11:39:45.230695

"""

# revision identifiers, used by Alembic.
revision = "529e8f6faed9"
down_revision = "12760875ee2d"
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.drop_constraint(
        "fk_analysisinterpretation_analysis_id_analysis",
        "analysisinterpretation",
        type_="foreignkey",
    )
    op.create_foreign_key(
        op.f("fk_analysisinterpretation_analysis_id_analysis"),
        "analysisinterpretation",
        "analysis",
        ["analysis_id"],
        ["id"],
        ondelete="CASCADE",
    )
    op.drop_constraint(
        "fk_analysisinterpretationsnapshot_analysisinterpretation_id_ana",
        "analysisinterpretationsnapshot",
        type_="foreignkey",
    )
    op.create_foreign_key(
        op.f("fk_analysisinterpretationsnapshot_analysisinterpretation_id_analysisinterpretation"),
        "analysisinterpretationsnapshot",
        "analysisinterpretation",
        ["analysisinterpretation_id"],
        ["id"],
        ondelete="CASCADE",
    )
    op.drop_constraint("fk_genotype_sample_id_sample", "genotype", type_="foreignkey")
    op.create_foreign_key(
        op.f("fk_genotype_sample_id_sample"),
        "genotype",
        "sample",
        ["sample_id"],
        ["id"],
        ondelete="CASCADE",
    )
    op.drop_constraint(
        "fk_genotypesampledata_sample_id_sample", "genotypesampledata", type_="foreignkey"
    )
    op.drop_constraint(
        "fk_genotypesampledata_genotype_id_genotype", "genotypesampledata", type_="foreignkey"
    )
    op.create_foreign_key(
        op.f("fk_genotypesampledata_genotype_id_genotype"),
        "genotypesampledata",
        "genotype",
        ["genotype_id"],
        ["id"],
        ondelete="CASCADE",
    )
    op.create_foreign_key(
        op.f("fk_genotypesampledata_sample_id_sample"),
        "genotypesampledata",
        "sample",
        ["sample_id"],
        ["id"],
        ondelete="CASCADE",
    )
    op.drop_constraint(
        "fk_interpretationlog_analysisinterpretation_id_analysisinterpre",
        "interpretationlog",
        type_="foreignkey",
    )
    op.create_foreign_key(
        op.f("fk_interpretationlog_analysisinterpretation_id_analysisinterpretation"),
        "interpretationlog",
        "analysisinterpretation",
        ["analysisinterpretation_id"],
        ["id"],
        ondelete="CASCADE",
    )
    op.drop_constraint(
        "fk_interpretationstatehistory_analysisinterpretation_id_analysi",
        "interpretationstatehistory",
        type_="foreignkey",
    )
    op.create_foreign_key(
        op.f("fk_interpretationstatehistory_analysisinterpretation_id_analysisinterpretation"),
        "interpretationstatehistory",
        "analysisinterpretation",
        ["analysisinterpretation_id"],
        ["id"],
        ondelete="CASCADE",
    )
    op.drop_constraint("fk_sample_analysis_id_analysis", "sample", type_="foreignkey")
    op.create_foreign_key(
        op.f("fk_sample_analysis_id_analysis"),
        "sample",
        "analysis",
        ["analysis_id"],
        ["id"],
        ondelete="CASCADE",
    )


def downgrade():
    op.drop_constraint(op.f("fk_sample_analysis_id_analysis"), "sample", type_="foreignkey")
    op.create_foreign_key(
        "fk_sample_analysis_id_analysis", "sample", "analysis", ["analysis_id"], ["id"]
    )
    op.drop_constraint(
        op.f("fk_interpretationstatehistory_analysisinterpretation_id_analysisinterpretation"),
        "interpretationstatehistory",
        type_="foreignkey",
    )
    op.create_foreign_key(
        "fk_interpretationstatehistory_analysisinterpretation_id_analysi",
        "interpretationstatehistory",
        "analysisinterpretation",
        ["analysisinterpretation_id"],
        ["id"],
    )
    op.drop_constraint(
        op.f("fk_interpretationlog_analysisinterpretation_id_analysisinterpretation"),
        "interpretationlog",
        type_="foreignkey",
    )
    op.create_foreign_key(
        "fk_interpretationlog_analysisinterpretation_id_analysisinterpre",
        "interpretationlog",
        "analysisinterpretation",
        ["analysisinterpretation_id"],
        ["id"],
    )
    op.drop_constraint(
        op.f("fk_genotypesampledata_sample_id_sample"), "genotypesampledata", type_="foreignkey"
    )
    op.drop_constraint(
        op.f("fk_genotypesampledata_genotype_id_genotype"), "genotypesampledata", type_="foreignkey"
    )
    op.create_foreign_key(
        "fk_genotypesampledata_genotype_id_genotype",
        "genotypesampledata",
        "genotype",
        ["genotype_id"],
        ["id"],
    )
    op.create_foreign_key(
        "fk_genotypesampledata_sample_id_sample",
        "genotypesampledata",
        "sample",
        ["sample_id"],
        ["id"],
    )
    op.drop_constraint(op.f("fk_genotype_sample_id_sample"), "genotype", type_="foreignkey")
    op.create_foreign_key(
        "fk_genotype_sample_id_sample", "genotype", "sample", ["sample_id"], ["id"]
    )
    op.drop_constraint(
        op.f("fk_analysisinterpretationsnapshot_analysisinterpretation_id_analysisinterpretation"),
        "analysisinterpretationsnapshot",
        type_="foreignkey",
    )
    op.create_foreign_key(
        "fk_analysisinterpretationsnapshot_analysisinterpretation_id_ana",
        "analysisinterpretationsnapshot",
        "analysisinterpretation",
        ["analysisinterpretation_id"],
        ["id"],
    )
    op.drop_constraint(
        op.f("fk_analysisinterpretation_analysis_id_analysis"),
        "analysisinterpretation",
        type_="foreignkey",
    )
    op.create_foreign_key(
        "fk_analysisinterpretation_analysis_id_analysis",
        "analysisinterpretation",
        "analysis",
        ["analysis_id"],
        ["id"],
    )
