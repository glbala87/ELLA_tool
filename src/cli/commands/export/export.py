import click
import logging

import datetime

from vardb.datamodel import DB
from vardb.export import export_sanger_variants, dump_classification

FILENAME_TIMESTAMP_FORMAT = "%Y-%m-%d_%H%M"  # 2017-11-10_1337


@click.group(help='Export data')
def export():
    pass


@export.command('classifications', help="Export all current classifications to excel and csv file.")
@click.option('--filename', help="The name of the file to create. Suffix .xls and .csv will be automatically added.\n"
                                  "Default: 'variant-classifications-YYYY-MM-DD_hhmm.xls/csv'")
@click.option('-with_analysis_names', is_flag=True,  help="Include name(s) of analysis where a variant is found")
def cmd_export_classifications(filename, with_analysis_names):
    """
    Exports all current classifications into an excel file.
    """
    logging.basicConfig(level=logging.INFO)

    today = datetime.datetime.now()
    timestamp = today.strftime(FILENAME_TIMESTAMP_FORMAT)
    output_name = filename if filename else "variant-classifications-{timestamp}".format(timestamp=timestamp)
    db = DB()
    db.connect()
    dump_classification.dump_alleleassessments(db.session, output_name, with_analysis_names)
    click.echo("Exported variants to " + output_name + '.xls/csv')

@export.command('sanger', help="Export variants that needs to be Sanger verified")
@click.option('--filename', help="The name of the file to create. Suffix .xls and .csv will be automatically added.\n"
                                  "Default: 'variant-sanger-YYYY-MM-DD_hhmm.xls/csv'")
def cmd_export_sanger(filename):
    """
    Export alleles from non-started analysis to file
    """
    logging.basicConfig(level=logging.INFO)
    today = datetime.datetime.now()
    timestamp = today.strftime(FILENAME_TIMESTAMP_FORMAT)
    output_name = filename if filename else "variant-sanger-{timestamp}".format(timestamp=timestamp)
    click.echo("Exporting variants to " + output_name + '.xls/csv')

    db = DB()
    db.connect()

    # Let exceptions propagate to user...
    excel_file_obj = open(filename + '.xls', 'w')
    csv_file_obj = open(filename + '.csv', 'w')

    has_content = export_sanger_variants.export_variants(
        db.session,
        excel_file_obj=excel_file_obj,
        csv_file_obj=csv_file_obj
    )

    if has_content:
        click.echo("Exported variants to " + output_name + '.xls/csv')
    else:
        csv_file_obj.write("# file is intentionally empty\n")
        excel_file_obj.write("file is intentionally empty")

    excel_file_obj.close()
    csv_file_obj.close()
