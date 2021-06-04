from typing import Any, List, Mapping, Sequence
import jsonschema
from dataclasses import dataclass, field
from sqlalchemy.orm import scoped_session
from vardb.datamodel.jsonschemas.load_schema import load_schema
from vardb.datamodel import annotation


@dataclass
class ConverterConfig:
    elements: Sequence[Mapping[str, Any]]


@dataclass(init=False)
class AnnotationImportConfig:
    name: str
    converter_config: ConverterConfig

    def __init__(self, name: str, converter_config: Mapping[str, Any]) -> None:
        self.name = name
        self.converter_config = ConverterConfig(**converter_config)


@dataclass(init=False)
class AnnotationConfig:
    deposit: Sequence[AnnotationImportConfig]
    view: List = field(default_factory=list)

    def __init__(self, deposit: Sequence[Mapping[str, Any]], view: List) -> None:
        self.view = view
        self.deposit = list()
        for sub_conf in deposit:
            self.deposit.append(AnnotationImportConfig(**sub_conf))


def deposit_annotationconfig(
    session: scoped_session, annotationconfig: Mapping[str, Any]
) -> annotation.AnnotationConfig:
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
