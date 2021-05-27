import jsonschema
from vardb.datamodel.jsonschemas.load_schema import load_schema
from vardb.datamodel import annotation


def deposit_annotationconfig(session, annotationconfig):
    schema = load_schema("annotationconfig.json")
    jsonschema.validate(annotationconfig, schema)

    ac_obj = annotation.AnnotationConfig(
        deposit=annotationconfig["deposit"], view=annotationconfig["view"]
    )
    session.add(ac_obj)
    session.flush()

    return ac_obj
