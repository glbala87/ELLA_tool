from flask import Flask, Response
from werkzeug.contrib.fixers import ProxyFix
from werkzeug.exceptions import HTTPException

from vardb.datamodel import DB

from applogger import setup_logger

setup_logger()

app = Flask(__name__)
app.wsgi_app = ProxyFix(app.wsgi_app)  # Sets REMOTE_ADDR from proxy headers etc


db = DB()
engine_kwargs = {"pool_size": 5, "max_overflow": 10, "pool_timeout": 30}
db.connect(engine_kwargs=engine_kwargs)


class ApiError(HTTPException):
    """
    Flask-restful documentation is very lacking when it comes to
    error handling. See source code of handle_error for
    a better understanding.
    """

    def __init__(self, message, status_code=500):
        HTTPException.__init__(self, message)
        self.code = status_code


class AuthenticationError(ApiError):
    def __init__(self, message, status_code=401):
        ApiError.__init__(self, message, status_code=status_code)


class ConflictError(ApiError):
    def __init__(self, message, status_code=409):
        ApiError.__init__(self, message, status_code=status_code)
