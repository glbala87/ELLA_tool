import click
import logging

from vardb.datamodel import DB
from vardb.export import dump_classification


@click.group(help='Export data')
def export():
    pass


@export.command('classifications')
@click.argument('output')
def cmd_export_classifications(output):
    """
    Exports all current classifications into a output excel file.
    """
    logging.basicConfig(level=logging.INFO)

    db = DB()
    db.connect()
    dump_classification.dump_alleleassessments(db.session, output)
