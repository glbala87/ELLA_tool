from flask import Flask

from vardb.datamodel import DB
from rest_query import RestQuery

app = Flask(__name__)
db = DB()
engine_kwargs = {
    "pool_size": 5,
    "max_overflow": 10,
    "pool_timeout": 30
}
db.connect(engine_kwargs=engine_kwargs, query_cls=RestQuery)


class ApiError(RuntimeError):
    pass
