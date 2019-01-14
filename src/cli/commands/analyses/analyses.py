import click
import logging
import json

from vardb.datamodel import DB, sample
from api.v1 import resources
from api.util.delete_analysis import delete_analysis
from vardb.deposit.deposit_analysis import import_filterconfigs


@click.group(help="Analyses actions")
def analyses():
    pass


@analyses.command("delete")
@click.argument("analysis_id", type=int)
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

    aname = (
        db.session.query(sample.Analysis.name).filter(sample.Analysis.id == analysis_id).one()[0]
    )

    answer = input(
        "Are you sure you want to delete analysis {}?\nType 'y' to confirm.\n".format(aname)
    )
    if answer == "y":
        try:
            delete_analysis(db.session, analysis_id)
            db.session.commit()
            click.echo("Analysis {} ({}) deleted successfully".format(analysis_id, aname))
        except Exception:
            logging.exception("Something went wrong while deleting analysis {}".format(analysis_id))
    else:
        click.echo("Lacking confirmation, aborting...")


@analyses.command("update_filterconfig")
@click.argument("filterconfig", type=click.File("r"))
def cmd_analysis_updatefilterconfig(filterconfig):
    """
    Updates filterconfigs from the input JSON file.
    """

    logging.basicConfig(level=logging.INFO)

    db = DB()
    db.connect()

    filterconfigs = json.load(filterconfig)
    result = import_filterconfigs(db.session, filterconfigs)

    db.session.commit()
    logging.info(
        "Created {} and updated {} filter configurations".format(
            result["created"], result["updated"]
        )
    )
