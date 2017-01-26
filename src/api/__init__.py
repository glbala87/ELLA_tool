from flask import Flask

from vardb.datamodel import DB
from rest_query import RestQuery

from polling import setup_polling

def create_app():
    app = Flask(__name__)
    setup_polling(app)
    return app

# Setup app, and create polling thread
app = create_app()

db = DB()
engine_kwargs = {
    "pool_size": 5,
    "max_overflow": 10,
    "pool_timeout": 30
}
db.connect(engine_kwargs=engine_kwargs, query_cls=RestQuery)


class ApiError(RuntimeError):
    pass
