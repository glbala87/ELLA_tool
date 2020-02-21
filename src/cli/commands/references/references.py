import click
import datetime

from pubmed.pubmed_fetcher import PubMedFetcher


@click.group(help="References actions")
def references():
    pass


@references.command("fetch")
@click.argument("pubmed_ids", type=click.Path(exists=True), required=True)
def cmd_references_fetch(pubmed_ids):

    d = datetime.datetime.now()

    output = "references-" + d.strftime("%y%m%d") + ".json"
    pm = PubMedFetcher()
    pm.get_references_from_file(pubmed_ids, dump_json=True, json_file=output)
