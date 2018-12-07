from flask import Flask, Response
from werkzeug.contrib.fixers import ProxyFix

from vardb.datamodel import DB


app = Flask(__name__)
app.wsgi_app = ProxyFix(app.wsgi_app)  # Sets REMOTE_ADDR from proxy headers etc


db = DB()
engine_kwargs = {
    "pool_size": 5,
    "max_overflow": 10,
    "pool_timeout": 30
}
db.connect(engine_kwargs=engine_kwargs)


class ApiError(RuntimeError):
    pass


class AuthenticationError(ApiError):
    def __init__(self, message, status_code=401):
        ApiError.__init__(self, message)
        self.status_code = status_code

class ConflictError(ApiError):
    def __init__(self, message, status_code=409):
        ApiError.__init__(self, message)
        self.status_code = status_code