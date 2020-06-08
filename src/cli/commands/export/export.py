import click
import datetime

from vardb.export import dump_classification

from cli.decorators import cli_logger, session

FILENAME_REPORT_DEFAULT = "non-started-analyses-variants-{timestamp}"

FILENAME_TIMESTAMP_FORMAT = "%Y-%m-%d_%H%M"  # 2017-11-10_1337


@click.group(help="Export data")
def export():
    pass


@export.command("classifications", help="Export all current classifications to excel and csv file.")
@click.option(
    "--filename",
    help="The name of the file to create. Suffix .xls and .csv will be automatically added.\n"
    "Default: 'variant-classifications-YYYY-MM-DD_hhmm.xlsx/csv'",
)
@click.option(
    "-with_analysis_names",
    is_flag=True,
    help="Include name(s) of analysis where a variant is found",
)
@session
@cli_logger()
def cmd_export_classifications(logger, session, filename, with_analysis_names):
    """
    Exports all current classifications into an excel file.
    """
    today = datetime.datetime.now()
    timestamp = today.strftime(FILENAME_TIMESTAMP_FORMAT)
    output_name = (
        filename if filename else "variant-classifications-{timestamp}".format(timestamp=timestamp)
    )
    dump_classification.dump_alleleassessments(session, output_name, with_analysis_names)
    logger.echo("Exported variants to " + output_name + ".xlsx/csv")
