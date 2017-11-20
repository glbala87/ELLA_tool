#!/usr/bin/env python
"""
Script for dropping all tables in a vardb database.
"""
from vardb.datamodel import *
from vardb.datamodel.annotationshadow import create_shadow_tables
from sqlalchemy.orm import configure_mappers


def make_db():

    db = DB()
    db.connect()
    configure_mappers()
    Base.metadata.create_all(db.engine)

    # Annotation shadow tables have extra logic, so we need to (re)create them
    create_shadow_tables(
        db.session,
        create_transcript=True,
        create_frequency=True
    )
    db.session.commit()

