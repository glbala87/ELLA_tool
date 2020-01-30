import click
import logging

from vardb.datamodel import DB, sample, workflow
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

    review_comment = (
        session.query(workflow.InterpretationLog.review_comment)
        .join(workflow.AnalysisInterpretation)
        .filter(workflow.AnalysisInterpretation.analysis_id == analysis_id)
        .filter(~workflow.InterpretationLog.review_comment.is_(None))
        .order_by(workflow.InterpretationLog.date_created.desc())
        .limit(1)
        .one_or_none()
    )

    if review_comment:
        overview_comment = "overview comment '{}'".format(review_comment[0])
    else:
        overview_comment = "no overview comment"

    workflow_status = (
        session.query(
            workflow.AnalysisInterpretation.status, workflow.AnalysisInterpretation.workflow_status
        )
        .filter(workflow.AnalysisInterpretation.analysis_id == analysis_id)
        .order_by(workflow.AnalysisInterpretation.id.desc())
        .limit(1)
        .one()
    )

    workflow_status = "{} ({})".format(*workflow_status)

    answer = input(
        "Are you sure you want to delete analysis {} with {} in workflow status: {}\nType 'y' to confirm.\n".format(
            aname, overview_comment, workflow_status
        )
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
