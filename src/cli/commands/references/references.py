import datetime
from pathlib import Path

import click
from pubmed.pubmed_fetcher import PubMedFetcher


@click.group(help="References actions")
def references():
    pass


@references.command("fetch")
@click.argument("pubmed_ids", type=click.Path(exists=True), required=True)
def cmd_references_fetch(pubmed_ids: str):

    d = datetime.datetime.now()

    output = Path("references-" + d.strftime("%y%m%d") + ".txt")
    pm = PubMedFetcher()
    pm.get_references_from_file(Path(pubmed_ids), output)
