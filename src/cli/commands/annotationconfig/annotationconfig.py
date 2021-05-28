import click
import json
import yaml

from vardb.datamodel import annotation
from vardb.deposit.deposit_annotationconfig import deposit_annotationconfig
from cli.decorators import cli_logger, session


@click.group(help="Annotation config management")
def annotationconfig():
    # noop
    ...


@annotationconfig.command("update")
@click.argument("annotationconfig", type=click.File("r"))
@session
@cli_logger(prompt_reason=True)
def cmd_update_annotationconfig(logger, session, annotationconfig):
    """
    Updates filterconfigs from the input JSON file.
    """

    annotationconfig = yaml.safe_load(annotationconfig)
    deposit_annotationconfig(session, annotationconfig)
    session.commit()
    print("Updated annotation config")


@annotationconfig.command("list")
@session
def list(session):

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
