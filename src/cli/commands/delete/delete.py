import click

from vardb.datamodel import sample, workflow, allele
from datalayer.queries import annotation_transcripts_genepanel
from api.schemas.alleleinterpretations import AlleleInterpretationOverviewSchema
from cli.decorators import cli_logger, session

from datetime import datetime


def delete_analysis(session, analysis_id):
    with session.no_autoflush:
        session.query(sample.Analysis).filter(sample.Analysis.id == analysis_id).delete()


@click.group(help="Delete actions")
def delete():
    pass


@delete.command("analysis")
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

    Does not delete any allele assessments.
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


@delete.command("alleleinterpretation")
@click.argument("allele_id", type=int)
@click.option("--delete-all", is_flag=True, help="List users that would be imported")
@session
@cli_logger(prompt_reason=True)
def cmd_alleleinterpretation_delete(logger, session, allele_id, delete_all):
    """
    Delete allele interpretations for a given allele_id. If --delete-all flag is set, then all
    allele interpretations are deleted. If not, then only allele interpretations since the allele
    was last finalized.

    Does not delete any allele assessments.
    """
    since_last_finalized = not delete_all

    # Find all allele interpretations to be deleted
    q = session.query(workflow.AlleleInterpretation).filter(
        workflow.AlleleInterpretation.allele_id == allele_id
    )
    total_count = q.count()
    if since_last_finalized:
        last_finalized = (
            q.filter(workflow.AlleleInterpretation.finalized.is_(True))
            .order_by(workflow.AlleleInterpretation.date_created.desc())
            .limit(1)
            .one_or_none()
        )
        if last_finalized:
            q = q.filter(workflow.AlleleInterpretation.date_created > last_finalized.date_created)

    if not q.count():
        logger.echo("Nothing to delete!")
        return

    # Logic to print out info to the user on what is to be deleted
    start_count = total_count - q.count()

    gp = q.first().genepanel
    genepanel_annotation = annotation_transcripts_genepanel(
        session, [(gp.name, gp.version)], allele_ids=[allele_id]
    ).subquery()

    annotations = session.query(
        genepanel_annotation.c.annotation_transcript,
        genepanel_annotation.c.annotation_symbol,
        genepanel_annotation.c.annotation_hgvsc,
    ).all()

    al = session.query(allele.Allele).filter(allele.Allele.id == allele_id).one()
    logger.echo("Ready to delete interpretations for allele:")
    logger.echo(str(al))
    if annotations:
        for tx, symbol, hgvsc in annotations:
            logger.echo("{}({}):{}".format(tx, symbol, hgvsc))
    else:
        logger.echo("(No available HGVSc annotations)")

    review_comment = (
        session.query(workflow.InterpretationLog.review_comment)
        .join(workflow.AlleleInterpretation)
        .filter(workflow.AlleleInterpretation.allele_id == allele_id)
        .filter(~workflow.InterpretationLog.review_comment.is_(None))
        .order_by(workflow.InterpretationLog.date_created.desc())
        .limit(1)
        .one_or_none()
    )
    if review_comment:
        overview_comment = "Overview comment '{}'".format(review_comment[0])
    else:
        overview_comment = "No overview comment"

    logger.echo("\n" + overview_comment + "\n")

    logger.echo("\nInterpretations to delete:")
    dumped_interpretations = AlleleInterpretationOverviewSchema().dump(q.all(), many=True)[0]
    for i, intp in enumerate(dumped_interpretations):
        s = f"{start_count + i+1} - {intp['workflow_status']}"
        if intp["status"] == "Ongoing":
            s += " (Ongoing)"
        elif intp["finalized"]:
            s += " (Finalized)"

        if intp.get("user"):
            s += f" - {intp.get('user').get('abbrev_name')} - {datetime.strftime(datetime.fromisoformat(intp['date_last_update']), '%Y-%m-%d %H:%M')}"
        logger.echo(s)

    # Confirm deletion
    answer = input(
        "Are you sure you want to delete these alleleinterpretations? \nType 'y' to confirm.\n"
    )

    if answer == "y":
        try:
            with session.no_autoflush:
                q.delete()
            session.commit()
            logger.echo("Interepretation(s) for allele {} deleted successfully".format(allele_id))
        except Exception:
            logger.exception("Something went wrong while deleting allele {}".format(allele_id))
    else:
        logger.echo("Lacking confirmation, aborting...")
