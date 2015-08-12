from sqlalchemy.orm import scoped_session
from flask import Flask

from vardb.datamodel import DB
from rest_query import RestQuery

app = Flask(__name__)
db = DB(query_cls=RestQuery)

session = scoped_session(db.sessionmaker)
