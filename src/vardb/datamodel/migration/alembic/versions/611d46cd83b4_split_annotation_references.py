"""foobar

Revision ID: 611d46cd83b4
Revises: 7fa4d0b48662
Create Date: 2021-01-12 11:18:09.435867

"""

# revision identifiers, used by Alembic.
revision = "611d46cd83b4"
down_revision = "7fa4d0b48662"
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa

from sqlalchemy.sql import table, column

# from sqlalchemy.dialects import postgresql
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm.session import Session
from vardb.datamodel.jsonschemas.update_schemas import update_schemas

Annotation = table("annotation", column("id", sa.Integer), column("annotations", JSONB))
CustomAnnotation = table("customannotation", column("id", sa.Integer), column("annotations", JSONB))


def upgrade():
    conn = op.get_bind()
    session = Session(bind=conn)
    # Drop trigger that disallows modification on annotation.annotations.
    # This needs to be added back.
    conn.execute("DROP TRIGGER annotation_to_annotationshadow ON annotation")

    # Drop trigger that cause a massive overhead
    # Need to update schemas after migration, so that the trigger is reinsterted
    conn.execute("DELETE from jsonschema where name='annotation'")
    conn.execute("DROP TRIGGER annotation_schema_version ON annotation")
    for tbl in [Annotation, CustomAnnotation]:
        annotations = conn.execute(sa.select([tbl.c.id, tbl.c.annotations]))
        for a in annotations:
            if "references" not in a.annotations:
                continue
            if tbl is Annotation:
                split_references = [
                    {
                        "source": source,
                        "pubmed_id": ref["pubmed_id"],
                        "source_info": ref["source_info"].get("source", ""),
                    }
                    for ref in a.annotations["references"]
                    for source in ref["sources"]
                ]
            elif tbl is CustomAnnotation:
                split_references = [
                    {"source": "User", "pubmed_id": ref.get("pubmed_id"), "id": ref["id"]}
                    for ref in a.annotations["references"]
                ]
            a.annotations["references"] = split_references

            conn.execute(
                sa.update(tbl).where(tbl.c.id == a.id).values({"annotations": a.annotations})
            )

    # Add back triggers
    conn.execute(
        "CREATE TRIGGER annotation_to_annotationshadow BEFORE INSERT OR UPDATE OR DELETE ON annotation FOR EACH ROW EXECUTE PROCEDURE annotation_to_annotationshadow();"
    )
    update_schemas(session)


def downgrade():

    conn = op.get_bind()
    session = Session(bind=conn)
    # Drop trigger that disallows modification on annotation.annotations.
    # This needs to be added back.
    conn.execute("DROP TRIGGER annotation_to_annotationshadow ON annotation")

    # Drop trigger that cause a massive overhead
    # Need to update schemas after migration, so that the trigger is reinsterted
    conn.execute("DELETE from jsonschema where name='annotation'")
    conn.execute("DROP TRIGGER annotation_schema_version ON annotation")
    for tbl in [Annotation, CustomAnnotation]:
        annotations = conn.execute(sa.select([tbl.c.id, tbl.c.annotations]))
        for a in annotations:
            if "references" not in a.annotations:
                continue
            if tbl is Annotation:
                merged_references = {}
                for ref in a.annotation["references"]:
                    if ref["pubmed_id"] in merged_references:
                        merged_references[ref["pubmed_id"]]["sources"].append(ref["source"])
                        merged_references[ref["pubmed_id"]]["source_info"][ref["source"]] = ref[
                            "source_info"
                        ]
                    else:
                        merged_references[ref["pubmed_id"]] = {
                            "sources": [ref["source"]],
                            "pubmed_id": ref["pubmed_id"],
                        }
                merged_references = [ref for ref in merged_references.values()]
            elif tbl is CustomAnnotation:
                merged_references = [
                    {"sources": ["User"], "pubmed_id": ref.get("pubmed_id"), "id": ref["id"]}
                    for ref in a.annotations["references"]
                ]
            a.annotations["references"] = merged_references

            conn.execute(
                sa.update(tbl).where(tbl.c.id == a.id).values({"annotations": a.annotations})
            )

    # Add back triggers
    conn.execute(
        "CREATE TRIGGER annotation_to_annotationshadow BEFORE INSERT OR UPDATE OR DELETE ON annotation FOR EACH ROW EXECUTE PROCEDURE annotation_to_annotationshadow();"
    )
    update_schemas(session)
