from collections import defaultdict
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


import click
import json

from vardb.datamodel import sample, user
from vardb.deposit.deposit_filterconfigs import deposit_filterconfigs
from cli.decorators import cli_logger, session
from datalayer.queries import get_usergroup_filter_configs
from sqlalchemy import literal, case
from api.util.util import query_print_table


from api.util.useradmin import (
    authenticate_user,
    create_session,
    change_password,
    logout,
    get_usersession_by_token,
)

from getpass import getpass
from api.v1.resources.workflow import helpers
from datalayer import queries
from vardb.datamodel import workflow


@export.command("analysis")
@click.argument("analysis_id", type=int)
@session
@cli_logger()
def analysis(logger, session, analysis_id):
    # username = input("username: ")
    # password = getpass("password: ")
    username = "testuser4"
    password = "demo"

    user = authenticate_user(session, username, password)
    interpretation = helpers._get_latest_interpretation(session, None, analysis_id)

    if interpretation.status != "Done":
        filter_config_id = queries.get_valid_filter_configs(
            session, user.group_id, interpretation.analysis_id
        )[0].id
    else:
        filter_config_id = None

    allele_ids, filtered_allele_ids, filter_config_id = helpers.get_filtered_alleles(
        session, interpretation, filter_config_id
    )

    all_interpretations = helpers.get_interpretations(
        session, user.group.genepanels, user.id, analysis_id=analysis_id
    )

    interpretation_log = helpers.get_interpretationlog(session, user.id, analysis_id=analysis_id)

    filter_config = (
        session.query(sample.FilterConfig).filter(sample.FilterConfig.id == filter_config_id).one()
    )

    # Sheets:
    # - Interpretation history + Interpretation log
    # - Info
    # - Classification
    # - Report
    #   - Analysis specific
    # - Filtered alleles (single or multiple sheets?)

    # Allele columns
    # - Gene
    # - HGVSc
    # - HGVSp
    # - Analysis specific
    # - Classification
    # - Classification date
    # - Evaluation
    # - Report
    # - Frequency
    # - External
    # - Prediction
    # - References
    # Annotation:
    # TBD

    ## Load alleles

    # alleles = dict()

    # alleles[(None, "unfiltered")] = helpers.get_alleles(
    #     session, allele_ids, user.group.genepanels, analysisinterpretation_id=interpretation.id
    # )

    # for i, filter in enumerate(filter_config.filterconfig["filters"]):
    #     alleles[(i, filter["name"])] = helpers.get_alleles(
    #         session,
    #         filtered_allele_ids[filter["name"]],
    #         user.group.genepanels,
    #         analysisinterpretation_id=interpretation.id,
    #     )

