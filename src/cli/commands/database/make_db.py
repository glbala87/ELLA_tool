#!/usr/bin/env python
"""
Script for creating all tables in a vardb database.
"""
from vardb.datamodel import *  # noqa: F403
from vardb.datamodel.annotationshadow import create_shadow_tables, create_tmp_shadow_tables
from vardb.datamodel.jsonschemas.update_schemas import update_schemas
from sqlalchemy.orm import configure_mappers
from api.config import config


def make_db(db):

    configure_mappers()
    Base.metadata.create_all(db.engine)  # noqa: F405

    refresh(db)


def refresh_tmp(db):
    # Although the annotationshadow tables were created above in create_all()
    # they have extra logic with triggers on dynamic fields, so we need to (re)create them
    create_tmp_shadow_tables(db.session, config)


def refresh(db, use_prepared_tmp_tables=False):
    # Add json schemas to table
    update_schemas(db.session)

    create_shadow_tables(db.session, config, use_prepared_tmp_tables=use_prepared_tmp_tables)
