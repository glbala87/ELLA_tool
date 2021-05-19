from vardb.datamodel import annotation


def deposit_annotationconfig(session, annotationconfig):
    ac_obj = annotation.AnnotationConfig(
        deposit=annotationconfig["deposit"], view=annotationconfig["view"]
    )
    session.add(ac_obj)
    session.flush()

    return ac_obj
