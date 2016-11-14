#!/usr/bin/env python
"""
Script for dropping all tables in a vardb database.
"""
import click
from .drop_db import drop_db
from .make_db import make_db
from .ci_migration_db import ci_migration_db_remake, ci_migration_upgrade_downgrade, ci_migration_head, make_migration_base_db
from .migration_db import migration_upgrade, migration_downgrade, migration_current


@click.group(help='Database management (create/drop/etc)')
def database():
    pass


@database.command('drop', help='Drops all data in database.')
@click.option('-f', is_flag=True, help='Do not ask for confirmation.')
def cmd_drop_db(f=None):
    if not f:
        answer = raw_input("Are you sure you want to DROP database?\nTHIS WILL DELETE ALL DATA!\nType 'DELETE ALL DATA' to cofirm.\n")
        if answer == 'DELETE ALL DATA':
            drop_db()
            click.echo("Database dropped!")
        else:
            click.echo("Lacking confirmation, aborting...")
    else:
        drop_db()
        click.echo("Database dropped!")


@database.command('make', help='Creates all tables in database.')
@click.option('-f', is_flag=True, help='Do not ask for confirmation.')
def cmd_make_db(f=None):
    if not f:
        answer = raw_input("Are you sure you want to create database tables?\nType 'CONFIRM' to confirm.\n")
        if answer == 'CONFIRM':
            make_db()
            click.echo("Tables successfully created")
        else:
            click.echo("Lacking confirmation, aborting...")
    else:
        make_db()
        click.echo("Tables successfully created")


@database.command('make-migration-base', help='Creates MIGRATION BASE tables in database. Useful when testing migration scripts manually.')
@click.option('-f', is_flag=True, help='Do not ask for confirmation.')
def cmd_make_db(f=None):
    if not f:
        answer = raw_input("Are you sure you want to create migration base(!) database tables?\nType 'CONFIRM' to confirm.\n")
        if answer == 'CONFIRM':
            make_migration_base_db()
            click.echo("Tables successfully created")
        else:
            click.echo("Lacking confirmation, aborting...")
    else:
        make_migration_base_db()
        click.echo("Tables successfully created")



@database.command('ci-migration', help='Runs migration upgrade/downgrade test')
def cmd_ci_migration_db():
    ci_migration_upgrade_downgrade()


@database.command('ci-migration-head', help='Creates base database then upgrades to head')
def cmd_ci_migration_db():
    ci_migration_head()


@database.command('ci-migration-base', help='Creates base database then upgrades to head')
def cmd_ci_migration_db():
    ci_migration_db_remake()


@database.command('upgrade', help='Upgrade database to revision.')
@click.argument('revision')
def cmd_upgrade(revision):
    migration_upgrade(revision)


@database.command('downgrade', help='Downgrade database to revision.')
@click.argument('revision')
def cmd_downgrade(revision):
    migration_downgrade(revision)


@database.command('current', help='Show current database revision.')
def cmd_current():
    migration_current()
