#!/usr/bin/env python
"""
Ella command line interface
"""
import os
import click
from cli.commands.broadcast.broadcast import broadcast
from cli.commands.database.database import database
from cli.commands.deposit.deposit import deposit
from cli.commands.analyses.analyses import analyses
from cli.commands.export.export import export
from cli.commands.users.users import users

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
cli_group.add_command(analyses)
cli_group.add_command(download_igv)
cli_group.add_command(export)
cli_group.add_command(users)

if __name__ == "__main__":
    cli_group()
