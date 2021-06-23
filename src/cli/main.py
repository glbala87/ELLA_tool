#!/usr/bin/env python
"""
Ella command line interface
"""
import os
import click
from cli.commands.broadcast.broadcast import broadcast
from cli.commands.database.database import database
from cli.commands.deposit.deposit import deposit
from cli.commands.export.export import export
from cli.commands.references.references import references
from cli.commands.users.users import users
from cli.commands.filterconfigs.filterconfigs import filterconfigs
from cli.commands.annotationconfig.annotationconfig import annotationconfig
from cli.commands.delete.delete import delete


SCRIPT_DIR = os.path.abspath(os.path.dirname(__file__))


@click.command("igv-download", help="Download IGV.js data")
@click.argument("target")
def download_igv(target):
    os.system(os.path.join(SCRIPT_DIR, "commands", "fetch-igv-data.sh") + " " + target)


@click.group()
def cli_group():
    pass


cli_group.add_command(broadcast)
cli_group.add_command(database)
cli_group.add_command(deposit)
cli_group.add_command(delete)
cli_group.add_command(download_igv)
cli_group.add_command(export)
cli_group.add_command(references)
cli_group.add_command(users)
cli_group.add_command(filterconfigs)
cli_group.add_command(annotationconfig)

if __name__ == "__main__":
    from applogger import setup_logger

    setup_logger()
    cli_group(prog_name="ella-cli")
