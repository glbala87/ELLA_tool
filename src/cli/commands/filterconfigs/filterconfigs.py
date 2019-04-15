import click
import logging
import json

from vardb.datamodel import DB, sample, user
from vardb.deposit.deposit_analysis import import_filterconfigs
from cli.decorators import cli_logger, session
from api.util.queries import get_usergroup_filter_configs, get_valid_filter_configs


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
    result = import_filterconfigs(session, filterconfigs)

    session.commit()
    logger.echo(
        "Created {} and updated {} filter configurations".format(
            result["created"], result["updated"]
        )
    )


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
