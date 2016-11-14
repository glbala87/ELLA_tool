#!/usr/bin/env python
"""
Ella command line interface
"""

import click
from commands.database.database import database
from commands.deposit.deposit import deposit


@click.group()
def cli():
    pass

cli.add_command(database)
cli.add_command(deposit)

if __name__ == '__main__':
    cli()
