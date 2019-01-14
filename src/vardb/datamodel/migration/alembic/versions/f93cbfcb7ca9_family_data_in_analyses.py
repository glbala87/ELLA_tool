"""Family data in analyses

Revision ID: f93cbfcb7ca9
Revises: 86deaf190356
Create Date: 2018-08-10 11:31:21.668868

"""

# revision identifiers, used by Alembic.
revision = "f93cbfcb7ca9"
down_revision = "86deaf190356"
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects import postgresql

from vardb.datamodel.migration.utils import update_enum


Genotype = sa.table(
    "genotype",
    sa.column("id", sa.Integer),
    sa.column("allele_id", sa.Integer),
    sa.column("secondallele_id", sa.Integer),
    sa.column("sample_id", sa.Integer),
    sa.column("homozygous", sa.Boolean),
    sa.column("genotype_quality", sa.Integer),
    sa.column("sequencing_depth", sa.Integer),
    sa.column("allele_depth", JSONB),
)

genotypesampledata_type = sa.Enum(
    "Homozygous", "Heterozygous", "Reference", "No coverage", name="genotypesampledata_type"
)

GenotypeSampleData = sa.table(
    "genotypesampledata",
    sa.column("genotype_id", sa.Integer),
    sa.column("secondallele", sa.Boolean),
    sa.column("multiallelic", sa.Boolean),
    sa.column("sample_id", sa.Integer),
    sa.column("type", genotypesampledata_type),
    sa.column("genotype_quality", sa.Integer),
    sa.column("genotype_likelihood", postgresql.ARRAY(sa.Integer())),
    sa.column("sequencing_depth", sa.Integer),
    sa.column("allele_depth", JSONB),
)

TABLE_NAMES = ["alleleinterpretationsnapshot", "analysisinterpretationsnapshot"]
OLD_OPTIONS = ["GENE", "FREQUENCY", "REGION"]
NEW_OPTIONS = OLD_OPTIONS + ["QUALITY", "SEGREGATION"]


def upgrade():
    # Update sample table
    with update_enum(
        op, TABLE_NAMES, "filtered", "interpretationsnapshot_filtered", OLD_OPTIONS, NEW_OPTIONS
    ) as tmp_tables:
        # We don't need to convert enums, we're only adding new ones
        pass

    conn = op.get_bind()
    sample_sex = sa.Enum("Male", "Female", name="sample_sex")
    sample_sex.create(conn, checkfirst=True)

    op.add_column(
        "sample", sa.Column("affected", sa.Boolean(), nullable=True)
    )  # Will be set as not null later
    op.add_column("sample", sa.Column("family_id", sa.String(), nullable=True))
    op.add_column("sample", sa.Column("father_id", sa.Integer(), nullable=True))
    op.add_column("sample", sa.Column("mother_id", sa.Integer(), nullable=True))
    op.add_column("sample", sa.Column("sibling_id", sa.Integer(), nullable=True))
    op.add_column(
        "sample", sa.Column("proband", sa.Boolean(), nullable=True)
    )  # Will be set as not null later
    op.add_column("sample", sa.Column("sex", sample_sex, nullable=True))
    op.create_foreign_key(
        op.f("fk_sample_father_id_sample"), "sample", "sample", ["father_id"], ["id"]
    )
    op.create_foreign_key(
        op.f("fk_sample_mother_id_sample"), "sample", "sample", ["mother_id"], ["id"]
    )
    op.create_foreign_key(
        op.f("fk_sample_sibling_id_sample"), "sample", "sample", ["sibling_id"], ["id"]
    )

    # Since we haven't supported family analyses yet, make all existing samples probands and affected
    conn.execute("UPDATE sample SET proband = true;")
    conn.execute("UPDATE sample SET affected = true;")

    op.alter_column("sample", "affected", nullable=False)
    op.alter_column("sample", "proband", nullable=False)

    # Create genotypesampledata
    op.create_table(
        "genotypesampledata",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("genotype_id", sa.Integer(), nullable=False),
        sa.Column("secondallele", sa.Boolean(), nullable=False),
        sa.Column("multiallelic", sa.Boolean(), nullable=False),
        sa.Column("type", genotypesampledata_type, nullable=False),
        sa.Column("sample_id", sa.Integer(), nullable=False),
        sa.Column("genotype_quality", sa.SmallInteger(), nullable=True),
        sa.Column("sequencing_depth", sa.SmallInteger(), nullable=True),
        sa.Column("genotype_likelihood", postgresql.ARRAY(sa.Integer()), nullable=True),
        sa.Column("allele_depth", postgresql.JSONB(), nullable=True),
        sa.ForeignKeyConstraint(
            ["genotype_id"],
            ["genotype.id"],
            name=op.f("fk_genotypesampledata_genotype_id_genotype"),
        ),
        sa.ForeignKeyConstraint(
            ["sample_id"], ["sample.id"], name=op.f("fk_genotypesampledata_sample_id_sample")
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_genotypesampledata")),
    )
    op.create_index(
        op.f("ix_genotypesampledata_sample_id"), "genotypesampledata", ["sample_id"], unique=False
    )

    # Migrate genotype -> genotypesampledata
    # This is rather simple for the single sample cases that we've supported so far.
    # Loop over all genotypes and construct genotypesampledata objects accordingly

    genotypes = conn.execute(sa.select([c for c in Genotype.c]))
    for g in genotypes:
        # For single samples, if secondallele exists, it's a multiallelic site
        multiallelic = bool(getattr(g, "secondallele_id"))
        # allele and secondallele (if it exists) has one row each
        for allele_field in ["allele_id", "secondallele_id"]:
            if getattr(g, allele_field):
                conn.execute(
                    GenotypeSampleData.insert().values(
                        genotype_id=g.id,
                        secondallele=allele_field == "secondallele_id",
                        multiallelic=multiallelic,
                        sample_id=g.sample_id,
                        type="Homozygous" if g.homozygous else "Heterozygous",
                        genotype_quality=g.genotype_quality,
                        sequencing_depth=g.sequencing_depth,
                        allele_depth=g.allele_depth,
                    )
                )

    # Clean up old columns
    op.drop_index("ix_genotype_analysis_id", table_name="genotype")
    op.drop_constraint("fk_genotype_analysis_id_analysis", "genotype", type_="foreignkey")
    op.drop_column("genotype", "sequencing_depth")
    op.drop_column("genotype", "genotype_quality")
    op.drop_column("genotype", "homozygous")
    op.drop_column("genotype", "analysis_id")
    op.drop_column("genotype", "allele_depth")


def downgrade():

    raise NotImplementedError("Downgrade not supported")
