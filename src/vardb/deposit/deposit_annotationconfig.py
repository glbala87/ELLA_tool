import jsonschema
from vardb.datamodel.jsonschemas.load_schema import load_schema
from vardb.datamodel import annotation


def deposit_annotationconfig(session, annotationconfig):
    schema = load_schema("annotationconfig.json")
    jsonschema.validate(annotationconfig, schema)

    active_annotationconfig = (
        session.query(annotation.AnnotationConfig)
        .order_by(annotation.AnnotationConfig.id.desc())
        .limit(1)
        .one_or_none()
    )

    # Check if annotation config is equal. Note that for deposit, we do not care about order or duplicity
    # Since the deposit is a list of dicts, we can not check set-equality (dicts are not hashable),
    # so we check that all items in incoming are in active, and vice versa.
    if (
        active_annotationconfig
        and all(x in active_annotationconfig.deposit for x in annotationconfig["deposit"])
        and all(x in annotationconfig["deposit"] for x in active_annotationconfig.deposit)
        and active_annotationconfig.view == annotationconfig["view"]
    ):
        raise RuntimeError("The annotation config matches the current active annotation config.")

    ac_obj = annotation.AnnotationConfig(
        deposit=annotationconfig["deposit"], view=annotationconfig["view"]
    )

    session.add(ac_obj)
    session.flush()

    return ac_obj
