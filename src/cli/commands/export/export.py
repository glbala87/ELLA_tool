import click
import logging

import datetime

from vardb.datamodel import DB, user, sample
from vardb.export import export_sanger_variants, dump_classification

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


@export.command("sanger", help="Export variants that needs to be Sanger verified")
@click.argument("user_group", required=True)
@click.option(
    "--filename",
    help="The name of the file to create. Suffix .xlsx and .csv will be automatically added.\n"
    "Default: '" + FILENAME_REPORT_DEFAULT.format(timestamp="YYYY-MM-DD_hhmm") + ".xlsx/csv'",
)
@session
@cli_logger()
def cmd_export_sanger(logger, session, user_group, filename):
    """
    Export alleles from non-started analysis to file
    """
    logging.basicConfig(level=logging.INFO)
    today = datetime.datetime.now()
    timestamp = today.strftime(FILENAME_TIMESTAMP_FORMAT)
    output_name = filename if filename else (FILENAME_REPORT_DEFAULT).format(timestamp=timestamp)
    logger.echo("Exporting variants to " + output_name + ".xlsx/csv")

    usergroup = session.query(user.UserGroup).filter(user.UserGroup.name == user_group).one()

    genepanels = [(g.name, g.version) for g in usergroup.genepanels]

    # Let exceptions propagate to user...
    excel_file_obj = open(output_name + ".xlsx", "wb")
    csv_file_obj = open(output_name + ".csv", "w")

    start = datetime.datetime.now()

    filter_config_id = (
        session.query(sample.FilterConfig.id)
        .join(sample.UserGroupFilterConfig)
        .filter(sample.UserGroupFilterConfig.usergroup_id == usergroup.id)
        .scalar()
    )

    has_content = export_sanger_variants.export_variants(
        session, genepanels, filter_config_id, excel_file_obj, csv_file_obj=csv_file_obj
    )
    if has_content:
        end = datetime.datetime.now()
        logger.echo(
            "Exported variants to " + output_name + ".xlsx/csv" + " in {}".format(str(end - start))
        )
    else:
        csv_file_obj.write("# file is intentionally empty\n")
        excel_file_obj.write(b"file is intentionally empty")

    excel_file_obj.close()
    csv_file_obj.close()
