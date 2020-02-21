import json
import os
import sys
import logging
import time
import datetime

from flask import send_from_directory, request, g, make_response
from flask_restful import Api
from api import app, db
from api.v1 import ApiV1
from api.util.util import populate_g_user, populate_g_logging, log_request

DEFAULT_STATIC_FILE = "index.html"
REWRITES = {"docs/": "docs/index.html", "docs": "docs/index.html"}
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

KEYWORD_DEVELOPER_MODE = "DEVELOP"
SCRIPT_DIR = os.path.abspath(os.path.dirname(__file__))
STATIC_FILE_DIR = os.path.join(SCRIPT_DIR, "../webui/build")
VALID_STATIC_FILES = [
    "app.css",
    "base.css",
    "app.js",
    "thirdparty.js",
    "templates.js",
    "fonts",
    "docs",
    "favicon.ico",
]

log = app.logger


@app.before_request
def populate_request():
    g.request_start_time = time.time() * 1000.0
    populate_g_logging()
    if request.path and request.path.split("/")[1] not in VALID_STATIC_FILES:
        populate_g_user()


@app.after_request
def after_request(response):
    if request.path and request.path.split("/")[1] not in VALID_STATIC_FILES:
        log_request(response.status_code, response)
        try:
            db.session.commit()
        except Exception:
            log.exception("Something went wrong when commiting resourcelog entry")
            db.session.rollback()

    return response


@app.teardown_request
def teardown_request(exc):
    if exc:
        # Gunicorn injects a [Errno 11] Resource temporarily unavailable error
        # into every request. We therefore ignore logging this error.
        # https://github.com/benoitc/gunicorn/issues/514
        if hasattr(exc, "errno") and exc.errno == 11:
            return
        log_request(500)
        try:
            db.session.commit()
        except Exception:
            log.exception("Something went wrong when commiting resourcelog entry")
            db.session.rollback()


@app.teardown_appcontext
def shutdown_session(exception=None):
    db.session.remove()


def serve_static(path=None):
    path = REWRITES.get(path, path)

    if not path:
        path = DEFAULT_STATIC_FILE

    if not any(v == path or path.startswith(v) for v in VALID_STATIC_FILES):
        path = DEFAULT_STATIC_FILE

    return send_from_directory(STATIC_FILE_DIR, path, cache_timeout=-1)


api = Api(app)


class DateTimeEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, datetime.datetime):
            return o.isoformat()

        return super().default(self, o)


# Turn off caching for whole API
@api.representation("application/json")
def output_json(data, code, headers=None):
    """Makes a Flask response with a JSON encoded body"""
    resp = make_response(json.dumps(data, cls=DateTimeEncoder), code)
    resp.headers.extend(headers or {})
    if "Cache-Control" not in resp.headers:
        resp.headers[
            "Cache-Control"
        ] = "no-store, no-cache, must-revalidate, post-check=0, pre-check=0"
    return resp


# Setup resources for v1
ApiV1(app, api).setup_api()

if os.environ.get("SERVE_STATIC"):
    app.add_url_rule("/", "index", serve_static)
    app.add_url_rule("/<path:path>", "index_redirect", serve_static)

# This is used by development - production will not trigger it
if __name__ == "__main__":
    opts = {"host": "0.0.0.0", "threaded": True, "port": int(os.getenv("API_PORT", "5000"))}

    # Dev mode stuff
    is_dev = os.getenv(KEYWORD_DEVELOPER_MODE, "").lower() == "true"
    if is_dev:
        opts["use_reloader"] = True

        # Enable remote debugging
        if os.environ.get("PTVS_PORT"):
            import ptvsd

            if os.environ.get("WERKZEUG_RUN_MAIN") == "true":
                print("Enabled python remote debugging at port {}".format(os.environ["PTVS_PORT"]))
                ptvsd.enable_attach(address=("0.0.0.0", os.environ["PTVS_PORT"]))

    if is_dev:
        print("!!!!!DEVELOPMENT MODE!!!!!")

    app.run(**opts)
