import click
import logging

import datetime

from vardb.datamodel import DB
from vardb.export import dump_classification

FILENAME_TIMESTAMP_FORMAT = "%Y-%m-%d_%H%M"  # 2017-11-10_1337


@click.group(help='Export data')
def export():
    pass


@export.command('classifications', help="Export all current classifications to excel and csv file.")
@click.option('--filename', help="The name of the file to created. Suffix .xls and .csv will be added.\n" 
                                  "Default: 'variant-classifications-YYYY-MM-DD_HHMM.xls/csv'")
def cmd_export_classifications(filename):
    """
    Exports all current classifications into an excel file.
    """
    logging.basicConfig(level=logging.INFO)

    today = datetime.datetime.now()
    timestamp = today.strftime(FILENAME_TIMESTAMP_FORMAT)
    output_name = filename if filename else "variant-classifications-{timestamp}".format(timestamp=timestamp)

    # return

    db = DB()
    db.connect()
    dump_classification.dump_alleleassessments(db.session, output_name)
    click.echo("Exported variants to " + output_name + '.xls/csv')
