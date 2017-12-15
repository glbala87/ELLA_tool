#!/usr/bin/env python
"""
Script for creating all tables in a vardb database.
"""
from vardb.datamodel import *
from vardb.datamodel.annotationshadow import create_shadow_tables
from sqlalchemy.orm import configure_mappers
from api.config import config


def make_db(db):

    configure_mappers()
    Base.metadata.create_all(db.engine)

    refresh(db)


def refresh(db):
    # Although the annotationshadow tables were created above in create_all()
    # they have extra logic with triggers on dynamic fields, so we need to (re)create them
    create_shadow_tables(
        db.session,
        config,
        create_transcript=True,
        create_frequency=True
    )
