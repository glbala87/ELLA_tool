import click
import json

from vardb.datamodel import sample, user
from vardb.deposit.deposit_filterconfigs import deposit_filterconfigs
from cli.decorators import cli_logger, session
from datalayer.queries import get_usergroup_filter_configs
from sqlalchemy import literal, case
from api.util.util import query_print_table


@click.group(help="Filter config management")
def filterconfigs():
    ...


@filterconfigs.command("update")
@click.argument("filterconfig", type=click.File("r"))
@session
@cli_logger(prompt_reason=True)
def cmd_analysis_updatefilterconfig(logger, session, filterconfig):
    """
    Updates filterconfigs from the input JSON file.
    """

    filterconfigs = json.load(filterconfig)
    result = deposit_filterconfigs(session, filterconfigs)
    changed = case(
        [
            (sample.FilterConfig.id.in_(result["fc_created"]), literal("Filterconfig created")),
            (sample.FilterConfig.id.in_(result["fc_updated"]), literal("Filterconfig updated")),
            (
                sample.UserGroupFilterConfig.id.in_(result["ugfc_created"]),
                literal("Added to usergroup"),
            ),
            (sample.UserGroupFilterConfig.id.in_(result["ugfc_updated"]), literal("Order changed")),
        ],
        else_=literal(""),
    )

    summary = (
        session.query(
            sample.FilterConfig.name,
            sample.UserGroupFilterConfig.order,
            user.UserGroup.name.label("usergroup"),
            changed.label("change"),
        )
        .join(sample.UserGroupFilterConfig)
        .join(user.UserGroup)
        .filter(sample.FilterConfig.active.is_(True))
        .order_by(user.UserGroup.name, sample.UserGroupFilterConfig.order)
    )

    logger.echo("\nSummary:\n")
    query_print_table(summary, logger.echo)

    session.commit()


@filterconfigs.command("deactivate")
@click.argument("filterconfig_id", type=int)
@session
@cli_logger(prompt_reason=True)
def deactivate(logger, session, filterconfig_id):
    filterconfig = (
        session.query(sample.FilterConfig).filter(sample.FilterConfig.id == filterconfig_id).one()
    )

    if not filterconfig.active:
        logger.echo("Filterconfig {} already inactive".format(filterconfig))
        return

    # Check that user group still has at least one active filter config
    usergroup_filterconfigs = get_usergroup_filter_configs(session, filterconfig.usergroup_id)
    if len(usergroup_filterconfigs.all()) == 1:
        logger.echo(
            "\n!!! You are about to disable the only active filter config for usergroup {} !!!\n".format(
                filterconfig.usergroup.name
            )
        )
    elif filterconfig.requirements == []:
        # Check that user group still has at least one active filter config without requirements
        noreq_filterconfigs = usergroup_filterconfigs.filter(
            sample.FilterConfig.requirements == []
        ).all()
        if len(noreq_filterconfigs) == 1:
            logger.echo(
                "\n!!! You are about to disable the only active filter config for usergroup {} without requirements !!!\n".format(
                    filterconfig.usergroup.name
                )
            )

    answer = input(
        "Are you sure you want to deactivate filter config {}?\nType 'y' to confirm.\n".format(
            filterconfig
        )
    )

    if answer == "y":
        filterconfig.active = False
        session.commit()
        logger.echo("Filterconfig {} deactivated".format(filterconfig.name))
    else:
        logger.echo("Lacking confirmation, aborting...")


@filterconfigs.command("list")
@session
def list(session):

    print("\nCurrent active filterconfigs:\n")

    q = (
        session.query(
            sample.FilterConfig.id,
            sample.FilterConfig.name,
            sample.UserGroupFilterConfig.order,
            user.UserGroup.name.label("usergroup"),
            sample.FilterConfig.requirements,
        )
        .join(sample.UserGroupFilterConfig)
        .join(user.UserGroup)
        .filter(sample.FilterConfig.active.is_(True))
        .order_by(user.UserGroup.name, sample.UserGroupFilterConfig.order)
    )

    query_print_table(q)
