#!/usr/bin/env python
"""
Script for dropping all tables in a vardb database.
"""
from vardb.datamodel import *

def drop_db():

    db = DB()
    db.connect()
    # Drop all tables, including alembic one...
    db.engine.execute('DROP SCHEMA public CASCADE')
    db.engine.execute('CREATE SCHEMA public')

