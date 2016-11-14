import click
import logging

from vardb.datamodel import DB, sample

from api.v1 import resources


@click.group(help='Analyses actions')
def analyses():
    pass


@analyses.command('list')
def cmd_analysis_list():
    """
    List latest imported analyses.
    """
    db = DB()
    db.connect()

    res = resources.analysis.AnalysisListResource()
    analyses = res.get(db.session)
    header = {'id': 'id', 'name': 'name', 'deposit_date': 'deposit_date', 'i_count': 'interp.', 'status': 'status'}
    row_format = "{id:^10}| {name:<50} | {deposit_date:^33} | {i_count:^7} | {status:^12} |"
    click.echo(row_format.format(**header))
    click.echo(row_format.format(**{'id': '-' * 10, 'name': '-' * 50, 'deposit_date': '-' * 33, 'i_count': '-' * 7, 'status': '-' * 12}))
    for a in analyses:
        # Add status to dict
        a['status'] = a['interpretations'][0]['status']
        a['i_count'] = len(a['interpretations'])
        click.echo(row_format.format(**{h: a[h] for h in header}))


@analyses.command('reopen')
@click.argument('analysis_id')
def cmd_analysis_reopen(analysis_id):
    """
    Reopens an analysis that is finalized.
    """
    logging.basicConfig(level=logging.INFO)

    db = DB()
    db.connect()

    res = resources.analysis.AnalysisActionReopenResource()
    res.post(db.session, analysis_id)
    logging.info("Analysis {} reopened successfully".format(analysis_id))


@analyses.command('delete')
@click.argument('analysis_id')
def cmd_analysis_delete(analysis_id):
    """
    Deletes an analysis, removing it's samples and genotypes
    in the process. Any alleles that were imported as part of the
    analysis are kept, as we cannot know which alleles that
    that only belongs to the analysis and which alleles that
    were also imported by other means.
    """
    logging.basicConfig(level=logging.INFO)

    db = DB()
    db.connect()

    aname = db.session.query(sample.Analysis.name).filter(sample.Analysis.id == analysis_id).one()[0]

    answer = raw_input("Are you sure you want to delete analysis {}?\nType 'y' to confirm.\n".format(aname))
    if answer == 'y':
        res = resources.analysis.AnalysisResource()
        try:
            res.delete(db.session, analysis_id, override=True)
            click.echo("Analysis {} deleted successfully".format(analysis_id))
        except Exception:
            logging.exception("Something went wrong while deleting analysis {}".format(analysis_id))
    else:
        click.echo("Lacking confirmation, aborting...")

