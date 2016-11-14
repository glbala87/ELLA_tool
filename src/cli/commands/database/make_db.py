#!/usr/bin/env python
"""
Script for dropping all tables in a vardb database.
"""
from vardb.datamodel import *

def make_db():

    db = DB()
    db.connect()
    Base.metadata.create_all(db.engine)

