#!/usr/bin/env python
"""
Functions for setting creating migration-base database,
then running all migrations until current head.

For CI and other testing purposes.
"""
from vardb.util import DB
from vardb.datamodel.migration.ci_migration_base import *  # Yes, use '*'
from .migration_db import migration_downgrade, migration_upgrade


def ci_migration_db_remake():
    db = DB()
    db.connect()

    # Drop all tables, including alembic one...
    db.engine.execute("DROP SCHEMA public CASCADE")
    db.engine.execute("CREATE SCHEMA public")
    Base.metadata.create_all(db.engine)


def ci_migration_upgrade_downgrade():
    ci_migration_head()
    migration_downgrade("base")


def ci_migration_head():
    ci_migration_db_remake()
    migration_upgrade("head")


def make_migration_base_db():

    db = DB()
    db.connect()
    Base.metadata.create_all(db.engine)
