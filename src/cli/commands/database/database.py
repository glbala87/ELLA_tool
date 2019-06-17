#!/usr/bin/env python
"""
Script for dropping all tables in a vardb database.
"""
import os
from contextlib import contextmanager
import click
import psycopg2

from vardb.datamodel import DB
from .drop_db import drop_db
from .make_db import make_db, refresh
from .ci_migration_db import (
    ci_migration_db_remake,
    ci_migration_upgrade_downgrade,
    ci_migration_head,
    make_migration_base_db,
)
from .migration_db import (
    migration_upgrade,
    migration_downgrade,
    migration_current,
    migration_history,
    migration_compare,
)
from cli.decorators import cli_logger


DEFAULT_WARNING = "THIS WILL WIPE OUT {} COMPLETELY! \nAre you sure you want to proceed? Type 'CONFIRM' to confirm.\n".format(
    os.environ.get("DB_URL")
)


@contextmanager
def confirm(echo_func, success_msg, force=False, warning=DEFAULT_WARNING):
    if not force:
        confirmation = input(warning)
        if confirmation == "CONFIRM":
            yield
            echo_func(success_msg)
        else:
            echo_func("Lacking confirmation, aborting...")
            raise RuntimeError("Lacking confirmation, aborting...")
    else:
        yield
        echo_func(success_msg)


@click.group(help="Database management (create/drop/migrate/etc)")
def database():
    pass


@database.command("drop", help="Drops all data in database.")
@click.option("-f", is_flag=True, help="Do not ask for confirmation.")
def cmd_drop_db(f=None):
    with confirm(click.echo, "Database dropped!", force=f):
        db = DB()
        db.connect()
        drop_db(db)


@database.command("make", help="Creates all tables in database.")
@click.option("-f", is_flag=True, help="Do not ask for confirmation.")
def cmd_make_db(f=None):
    with confirm(click.echo, "Tables should now have been created.", force=f):
        db = DB()
        db.connect()
        make_db(db)
        db.session.commit()


@database.command("refresh", help="Refresh shadow tables in database.")
@click.option("-f", is_flag=True, help="Do not ask for confirmation.")
@cli_logger()
def cmd_refresh(logger, f=None):
    warning = "This will refresh all shadow tables in the database. Do not run this command while app is running.\nType 'CONFIRM' to confirm.\n"
    with confirm(logger.echo, "Tables should now have been refreshed.", force=f, warning=warning):
        db = DB()
        db.connect()
        logger.echo("Refreshing shadow tables and (re)creating triggers.")
        refresh(db)
        logger.echo("Done!")
        db.session.commit()
        ast_count = list(db.session.execute("SELECT COUNT(*) FROM annotationshadowtranscript"))[0][
            0
        ]
        asf_count = list(db.session.execute("SELECT COUNT(*) FROM annotationshadowfrequency"))[0][0]
        db.disconnect()

        conn = psycopg2.connect(os.environ["DB_URL"])
        conn.set_isolation_level(psycopg2.extensions.ISOLATION_LEVEL_AUTOCOMMIT)
        conn.cursor().execute("VACUUM(ANALYZE)")

        logger.echo("AnnotationShadowTranscript count: {}".format(ast_count))
        logger.echo("AnnotationShadowFrequency count: {}".format(asf_count))


@database.command(
    "make-migration-base",
    help="Creates MIGRATION BASE tables in database.",
    short_help="Create database from migration base",
)
@click.option("-f", is_flag=True, help="Do not ask for confirmation.")
def cmd_make_migration_base(f=None):
    with confirm(click.echo, "Tables should now have been created.", force=f):
        make_migration_base_db()


@database.command(
    "ci-migration-test",
    help="Runs all migrations through upgrades followed by downgrades",
    short_help="Runs all migrations up and down",
)
@click.option("-f", is_flag=True, help="Do not ask for confirmation.")
def cmd_ci_migration(f=None):
    with confirm(click.echo, "Migrations completed successfully", force=f):
        ci_migration_upgrade_downgrade()


@database.command(
    "ci-migration-head",
    help="Creates base database then upgrades to newest revision",
    short_help="From base to newest revision",
)
@click.option("-f", is_flag=True, help="Do not ask for confirmation.")
def cmd_ci_migration_head(f=None):
    with confirm(click.echo, "Migrations to newest revision was successful.", force=f):
        ci_migration_head()


@database.command("ci-migration-base", help="Creates base database tables")
@click.option("-f", is_flag=True, help="Do not ask for confirmation.")
def cmd_migration_base(f=None):
    with confirm(click.echo, "Base database tables created successfully.", force=f):
        ci_migration_db_remake()


@database.command(
    "upgrade",
    help="Upgrade database from current to a specific revision.",
    short_help="Upgrade to version",
)
@click.argument("revision")
@cli_logger()
def cmd_upgrade(logger, revision):
    migration_upgrade(revision)


@database.command(
    "downgrade",
    help="Downgrade database from current to a specific revision.",
    short_help="Downgrade to version",
)
@click.argument("revision")
@cli_logger()
def cmd_downgrade(logger, revision):
    migration_downgrade(revision)


@database.command("current", help="Show revision of current migration.", short_help="Show current")
def cmd_current():
    migration_current()


@database.command(
    "history", help="Show all migrations that have been applied", short_help="Show all migrations"
)
@click.option("-v", is_flag=True, help="Verbose: more details.")
@click.option("--range", help="Revision range")
def cmd_history(v, range):
    migration_history(range=range, verbose=v)


@database.command(
    "compare",
    help="Compares database HEAD revision to migration script HEAD revision. Error on mismatch.",
    short_help="Compare current DB and script revisions.",
)
def cmd_migration_compare():
    migration_compare()


@database.command(
    "make-production",
    help="Initializes an empty database for production.",
    short_help="Create production db",
)
@click.option("-f", is_flag=True, help="Do not ask for confirmation.")
def cmd_make_production(f=None):
    with confirm(click.echo, "Tables should now have been created.", force=f):
        db = DB()
        db.connect()
        table_count = list(
            db.session.execute(
                "select count(*) from information_schema.tables where table_schema = 'public'"
            )
        )[0][0]
        assert table_count == 0, "Database schema 'public' is not empty."
        make_migration_base_db()
        migration_upgrade("head")
        click.echo("Refreshing shadow tables and (re)creating triggers.")
        refresh(db)
        db.session.commit()
        click.echo("All done!")
