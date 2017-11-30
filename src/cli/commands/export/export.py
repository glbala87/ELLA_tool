import click
import logging

import datetime

from vardb.datamodel import DB
from vardb.export import dump_sanger_variants, dump_classification

FILENAME_TIMESTAMP_FORMAT = "%Y-%m-%d_%H%M"  # 2017-11-10_1337


@click.group(help='Export data')
def export():
    pass


@export.command('classifications', help="Export all current classifications to excel and csv file.")
@click.option('--filename', help="The name of the file to create. Suffix .xls and .csv will be automatically added.\n" 
                                  "Default: 'variant-classifications-YYYY-MM-DD_hhmm.xls/csv'")
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


@export.command('sanger', help="Export variants that needs to be Sanger verified")
@click.option('--filename', help="The name of the file to create. Suffix .xls and .csv will be automatically added.\n" 
                                  "Default: 'variant-sanger-YYYY-MM-DD_hhmm.xls/csv'")
def cmd_export_variants(filename):
    """
    Exports all current classifications into an excel file.
    """
    logging.basicConfig(level=logging.INFO)

    today = datetime.datetime.now()
    timestamp = today.strftime(FILENAME_TIMESTAMP_FORMAT)
    output_name = filename if filename else "variant-sanger-{timestamp}".format(timestamp=timestamp)

    # return

    db = DB()
    db.connect()
    dump_sanger_variants.dump_variants(db.session, output_name)
    click.echo("Exported variants to " + output_name + '.xls/csv')
