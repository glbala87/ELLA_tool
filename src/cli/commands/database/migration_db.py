#!/usr/bin/env python

import os
import sys
from alembic.script import ScriptDirectory
from alembic.migration import MigrationContext
from alembic.config import Config
from alembic import command

from vardb.util import DB

SCRIPT_DIR = os.path.dirname(os.path.realpath(__file__))
ALEMBIC_CFG = os.path.join(SCRIPT_DIR, "../../../vardb/datamodel/migration/alembic.ini")
ALEMBIC_DIR = os.path.join(SCRIPT_DIR, "../../../vardb/datamodel/migration/alembic/")


def _get_alembic_config():
    alembic_cfg = Config(ALEMBIC_CFG)
    alembic_cfg.set_main_option("script_location", ALEMBIC_DIR)
    return alembic_cfg


def migration_upgrade(rev):
    alembic_cfg = _get_alembic_config()
    db = DB()
    db.connect()
    with db.engine.begin() as connection:
        alembic_cfg.attributes["connection"] = connection
    command.upgrade(alembic_cfg, rev)


def migration_downgrade(rev):
    alembic_cfg = _get_alembic_config()
    db = DB()
    db.connect()
    with db.engine.begin() as connection:
        alembic_cfg.attributes["connection"] = connection
        command.downgrade(alembic_cfg, rev)


def migration_current():
    alembic_cfg = _get_alembic_config()
    db = DB()
    db.connect()
    with db.engine.begin() as connection:
        alembic_cfg.attributes["connection"] = connection
        command.current(alembic_cfg)


def migration_history(range=None, verbose=False):
    alembic_cfg = _get_alembic_config()
    db = DB()
    db.connect()
    with db.engine.begin() as connection:
        alembic_cfg.attributes["connection"] = connection
        command.history(alembic_cfg, rev_range=range, verbose=verbose)


def migration_compare():
    alembic_cfg = _get_alembic_config()
    db = DB()
    db.connect()
    with db.engine.begin() as connection:
        context = MigrationContext.configure(connection)
        db_head_rev = context.get_current_revision()

        alembic_cfg.attributes["connection"] = connection
        script = ScriptDirectory.from_config(alembic_cfg)
        script_rev_head = script.get_current_head()

        print("Database HEAD: {}".format(db_head_rev))
        print("Migration script HEAD: {}".format(script_rev_head))
        if not db_head_rev == script_rev_head:
            print("Database HEAD does not match migration script HEAD!")
            sys.exit(1)
        else:
            print("Migration status OK!")
