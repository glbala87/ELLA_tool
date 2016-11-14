#!/usr/bin/env python

import os
from alembic.config import Config
from alembic import command

from vardb.util import DB

SCRIPT_DIR = os.path.dirname(os.path.realpath(__file__))
ALEMBIC_CFG = os.path.join(SCRIPT_DIR, '../../../datamodel/migration/alembic.ini')
ALEMBIC_DIR = os.path.join(SCRIPT_DIR, '../../../datamodel/migration/alembic/')


def _get_alembic_config():
    alembic_cfg = Config(ALEMBIC_CFG)
    alembic_cfg.set_main_option("script_location", ALEMBIC_DIR)
    return alembic_cfg


def migration_upgrade(rev):
    alembic_cfg = _get_alembic_config()
    db = DB()
    db.connect()
    with db.engine.begin() as connection:
        alembic_cfg.attributes['connection'] = connection
    command.upgrade(alembic_cfg, rev)


def migration_downgrade(rev):
    alembic_cfg = _get_alembic_config()
    db = DB()
    db.connect()
    with db.engine.begin() as connection:
        alembic_cfg.attributes['connection'] = connection
        command.downgrade(alembic_cfg, rev)


def migration_current():
    alembic_cfg = _get_alembic_config()
    db = DB()
    db.connect()
    with db.engine.begin() as connection:
        alembic_cfg.attributes['connection'] = connection
        command.current(alembic_cfg)
