#!/usr/bin/env python
"""
Script for dropping all tables in a vardb database.
"""
from vardb.datamodel import *
from sqlalchemy.orm import configure_mappers


def make_db():

    db = DB()
    db.connect()
    configure_mappers()
    Base.metadata.create_all(db.engine)

