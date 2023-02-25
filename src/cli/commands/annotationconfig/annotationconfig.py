import json
from logging import Logger
from typing import Any, Dict

import click
import yaml
from cli.decorators import cli_logger, session
from sqlalchemy.orm import scoped_session
from vardb.datamodel import annotation
from vardb.deposit.annotation_config import deposit_annotationconfig


@click.group(help="Annotation config management")
def annotationconfig():
    # noop
    ...


@annotationconfig.command("update")
@click.argument("annotationconfig", type=click.File("r"))
@session
@cli_logger(prompt_reason=True)
def cmd_update_annotationconfig(logger: Logger, session: scoped_session, annotationconfig: str):
    """
    Updates annotationconfigs from the input YAML file.
    """

    config_obj: Dict[str, Any] = yaml.safe_load(annotationconfig)
    deposit_annotationconfig(session, config_obj)
    session.commit()
    print("Updated annotation config")


@annotationconfig.command("list")
@session
def list(session: scoped_session):
    print("\nCurrent active annotationconfig:\n")

    active_annotationconfig = (
        session.query(annotation.AnnotationConfig)
        .order_by(annotation.AnnotationConfig.id.desc())
        .limit(1)
        .one_or_none()
    )
    print("Deposit:\n")
    print(json.dumps(active_annotationconfig.deposit, indent=4))
    print("View:\n")
    print(json.dumps(active_annotationconfig.view, indent=4))
