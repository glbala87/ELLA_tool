#!/usr/bin/env python
"""
Ella command line interface
"""

import click
from commands.database.database import database


@click.group()
def cli():
    pass

cli.add_command(database)

if __name__ == '__main__':
    cli()
