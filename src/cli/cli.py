#!/usr/bin/env python
"""
Ella command line interface
"""

import click
from commands.database.database import database
from commands.deposit.deposit import deposit
from commands.analyses.analyses import analyses


@click.group()
def cli():
    pass

cli.add_command(database)
cli.add_command(deposit)
cli.add_command(analyses)

if __name__ == '__main__':
    cli()
