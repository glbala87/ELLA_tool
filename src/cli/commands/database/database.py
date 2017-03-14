#!/usr/bin/env python
"""
Script for dropping all tables in a vardb database.
"""
import os
import click
from .drop_db import drop_db
from .make_db import make_db
from .ci_migration_db import ci_migration_db_remake, ci_migration_upgrade_downgrade, ci_migration_head, make_migration_base_db
from .migration_db import migration_upgrade, migration_downgrade, migration_current


def confirm(func, success_msg, force=False):
    if not force:
        confirmation = raw_input("THIS WILL WIPE OUT {} COMPLETELY! \nAre you sure you want to proceed? Type 'CONFIRM' to confirm.\n".format(os.environ.get('DB_URL')))
        if confirmation == 'CONFIRM':
            func()
            click.echo(success_msg)
        else:
            click.echo("Lacking confirmation, aborting...")
    else:
        func()
        click.echo(success_msg)


@click.group(help='Database management (create/drop/etc)')
def database():
    pass


@database.command('drop', help='Drops all data in database.')
@click.option('-f', is_flag=True, help='Do not ask for confirmation.')
def cmd_drop_db(f=None):
    confirm(drop_db, "Database dropped!", force=f)


@database.command('make', help='Creates all tables in database.')
@click.option('-f', is_flag=True, help='Do not ask for confirmation.')
def cmd_make_db(f=None):
    confirm(make_db, "Tables should now have been created.", force=f)


@database.command('make-migration-base', help='Creates MIGRATION BASE tables in database. Useful when testing migration scripts manually.')
@click.option('-f', is_flag=True, help='Do not ask for confirmation.')
def cmd_make_migration_base(f=None):
    confirm(make_migration_base_db, "Tables should now have been created.", force=f)


@database.command('ci-migration-test', help='Runs migration upgrade/downgrade test')
@click.option('-f', is_flag=True, help='Do not ask for confirmation.')
def cmd_ci_migration(f=None):
    confirm(ci_migration_upgrade_downgrade, 'Test completed successfully', force=f)


@database.command('ci-migration-head', help='Creates base database then upgrades to head')
@click.option('-f', is_flag=True, help='Do not ask for confirmation.')
def cmd_ci_migration_head(f=None):
    confirm(ci_migration_head, 'Tables upgraded successfully.', force=f)


@database.command('ci-migration-base', help='Creates migration base database tables')
@click.option('-f', is_flag=True, help='Do not ask for confirmation.')
def cmd_ci_migration_base(f=None):
    confirm(ci_migration_db_remake, 'Tables created successfully.', force=f)


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
