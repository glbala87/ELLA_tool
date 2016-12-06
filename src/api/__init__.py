from flask import Flask
from werkzeug.routing import BaseConverter
from werkzeug.serving import is_running_from_reloader

from vardb.datamodel import DB
from rest_query import RestQuery

from polling import setup_polling

def create_app():
    app = Flask(__name__)
    setup_polling(app)
    return app

# Setup app, and create polling thread
app = create_app()

class ListConverter(BaseConverter):
    def to_python(self, value):
        return value.split(',')

    def to_url(self, values):
        return ','.join(BaseConverter.to_url(value)
                        for value in values)

app.url_map.converters['list'] = ListConverter

db = DB()
engine_kwargs = {
    "pool_size": 5,
    "max_overflow": 10,
    "pool_timeout": 30
}
db.connect(engine_kwargs=engine_kwargs, query_cls=RestQuery)


class ApiError(RuntimeError):
    pass
