"""Support gene panels from GPB (Gene Panel Builder)

Revision ID: 88b3cbf57659
Revises: 1675e8d8b078
Create Date: 2023-02-14 10:19:42.569913

"""

# revision identifiers, used by Alembic.
revision = "88b3cbf57659"
down_revision = "1675e8d8b078"
branch_labels = None
depends_on = None

from dataclasses import dataclass
from typing import Set

from alembic import op


def compute_consensus_inheritance(inheritances: Set[str]):
    if inheritances == {"AD"}:
        return "AD"
    elif inheritances == {"AR"}:
        return "AR"
    elif inheritances == {"XD"}:
        return "XD"
    elif inheritances == {"XR"}:
        return "XR"
    elif any(inh.startswith("X") for inh in inheritances):
        return "XD/XR"
    return "AD/AR"


def legacy_distinct_inheritance_hgnc_ids(conn, genepanel_name, genepanel_version, inheritance):
    "Equal to queries.legacy_distinct_inheritance_hgnc_ids at time of writing"
    res = conn.execute(
        f"""
        SELECT phenotype.gene_id AS hgnc_id
        FROM phenotype, genepanel_phenotype AS gp_phenotype
        WHERE phenotype.id = gp_phenotype.phenotype_id
        AND gp_phenotype.genepanel_name = '{genepanel_name.replace("%", "%%")}'
        AND gp_phenotype.genepanel_version = '{genepanel_version}'
        GROUP BY gp_phenotype.genepanel_name, gp_phenotype.genepanel_version, phenotype.gene_id
        HAVING every(phenotype.inheritance = '{inheritance}')
        """
    ).fetchall()

    return set([r[0] for r in res])


def new_distinct_inheritance_hgnc_ids(conn, genepanel_name, genepanel_version, inheritance):
    "Get all hgnc ids matching 'inheritance' from the genepanel_transcript table"
    res = conn.execute(
        f"""
        SELECT gene_id FROM transcript WHERE id in (
            SELECT DISTINCT transcript_id
            FROM genepanel_transcript
            WHERE genepanel_name = '{genepanel_name.replace("%", "%%")}'
            AND genepanel_version = '{genepanel_version}'
            AND inheritance = '{inheritance}'
        );
        """
    )
    return set(x[0] for x in res)


@dataclass
class TranscriptInheritance:
    transcript_id: str
    inheritance: str


def upgrade():
    # Loop over all gene panels
    # For each gene panel, loop over all transcripts
    # For each gene in gene panel, get all phenotypes
    # Compute consensus inheritance
    # Add consensus inheritance to genepanel_transcript entry
    conn = op.get_bind()

    conn.execute("ALTER TABLE genepanel_transcript ADD COLUMN inheritance text")

    genepanels = conn.execute("SELECT name, version FROM genepanel").fetchall()

    for genepanel_name, genepanel_version in genepanels:
        # Update genepanel_transcript table with consensus inheritance
        # from genepanel phenotypes for each gene

        # Get all inheritances for each gene in the genepanel, from the phenotype-table
        hgnc_id_inheritances = conn.execute(
            f"""
            SELECT gene_id, array_agg(inheritance) FROM phenotype WHERE id IN (
                SELECT DISTINCT phenotype_id
                FROM genepanel_phenotype
                WHERE genepanel_name = '{genepanel_name.replace("%", "%%")}'
                AND genepanel_version = '{genepanel_version}'
            )
            GROUP BY gene_id
            """
        ).fetchall()

        # Get all transcripts for each gene in the genepanel
        hgnc_id_transcript_ids = conn.execute(
            f"""
            SELECT gene_id, id FROM transcript WHERE id IN (
                SELECT DISTINCT transcript_id
                FROM genepanel_transcript
                WHERE genepanel_name = '{genepanel_name.replace("%", "%%")}'
                AND genepanel_version = '{genepanel_version}'
            )
            """,
        ).fetchall()

        # Some genes have no transcript in the genepanel, but have phenotypes - these will not have an inheritance
        # in the genepanel_transcript table
        inheritance_without_transcript = set(x[0] for x in hgnc_id_inheritances) - set(
            x[0] for x in hgnc_id_transcript_ids
        )

        inheritance_by_hgnc_id = dict(hgnc_id_inheritances)

        # Compute consensus inheritance for each gene, to be added to genepanel_transcript table
        new_inheritance_tx_id = []
        for hgnc_id, transcript_id in hgnc_id_transcript_ids:
            consensus_inheritance = compute_consensus_inheritance(
                set(inheritance_by_hgnc_id.get(hgnc_id, []))
            )

            new_inheritance_tx_id.append(
                TranscriptInheritance(str(transcript_id), consensus_inheritance)
            )

            # new_inheritance_by_tx_id[str(transcript_id)] = f"'{consensus_inheritance}'"

        # Batch update genepanel_transcript-table
        conn.execute(
            f"""
            update "genepanel_transcript"
            set inheritance = data_table.inheritance
            from
                (select
                    unnest(array[{','.join(map(lambda x: str(x.transcript_id), new_inheritance_tx_id))}]) as transcript_id,
                    unnest(array[{','.join(map(lambda x: f"'{x.inheritance}'", new_inheritance_tx_id))}]) as inheritance
                ) as data_table
            where genepanel_transcript.transcript_id = data_table.transcript_id
            and genepanel_name = '{genepanel_name.replace("%", "%%")}'
            and genepanel_version = '{genepanel_version}';
            """
        )

        # Compare distinct inheritance genes before and after
        # These should match, with the exception of genes with no transcript in the genepanel
        legacy_ar_genes = legacy_distinct_inheritance_hgnc_ids(
            conn, genepanel_name, genepanel_version, "AR"
        )
        legacy_ad_genes = legacy_distinct_inheritance_hgnc_ids(
            conn, genepanel_name, genepanel_version, "AD"
        )
        new_ar_genes = new_distinct_inheritance_hgnc_ids(
            conn, genepanel_name, genepanel_version, "AR"
        )
        new_ad_genes = new_distinct_inheritance_hgnc_ids(
            conn, genepanel_name, genepanel_version, "AD"
        )

        assert legacy_ad_genes - inheritance_without_transcript == new_ad_genes
        assert legacy_ar_genes - inheritance_without_transcript == new_ar_genes

        # Ensure that we have set inheritance on all genepanel transcripts
        null_inheritance_count = conn.execute(
            f"""
            SELECT count(*)
            FROM genepanel_transcript
            WHERE inheritance is null
            AND genepanel_name='{genepanel_name.replace("%", "%%")}'
            AND genepanel_version='{genepanel_version}'
            """
        ).first()[0]
        assert null_inheritance_count == 0

    conn.execute("ALTER TABLE genepanel_transcript ALTER COLUMN inheritance SET NOT NULL")
    conn.execute("ALTER TABLE transcript ADD COLUMN tags text[]")
    conn.execute("ALTER TABLE transcript DROP COLUMN corresponding_refseq")
    conn.execute("ALTER TABLE transcript DROP COLUMN corresponding_ensembl")
    conn.execute("ALTER TABLE transcript DROP COLUMN corresponding_lrg")
    conn.execute("ALTER TABLE gene DROP column omim_entry_id")
    conn.execute("ALTER TABLE gene DROP column ensembl_gene_id")


def downgrade():
    # Downgrade not supported, since we no longer have the information (e.g. corresponding_ensembl)
    raise NotImplementedError("Downgrade not supported")
