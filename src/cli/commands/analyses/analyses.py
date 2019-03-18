import click
import logging

from vardb.datamodel import DB, sample
from api.util.delete_analysis import delete_analysis
from cli.decorators import cli_logger, session


@click.group(help="Analyses actions")
def analyses():
    pass


@analyses.command("delete")
@click.argument("analysis_id", type=int)
@session
@cli_logger(prompt_reason=True)
def cmd_analysis_delete(logger, session, analysis_id):
    """
    Deletes an analysis, removing it's samples and genotypes
    in the process. Any alleles that were imported as part of the
    analysis are kept, as we cannot know which alleles that
    that only belongs to the analysis and which alleles that
    were also imported by other means.
    """

    aname = session.query(sample.Analysis.name).filter(sample.Analysis.id == analysis_id).one()[0]

    answer = input(
        "Are you sure you want to delete analysis {}?\nType 'y' to confirm.\n".format(aname)
    )
    if answer == "y":
        try:
            delete_analysis(session, analysis_id)
            session.commit()
            logger.echo("Analysis {} ({}) deleted successfully".format(analysis_id, aname))
        except Exception:
            logger.exception("Something went wrong while deleting analysis {}".format(analysis_id))
    else:
        logger.echo("Lacking confirmation, aborting...")
