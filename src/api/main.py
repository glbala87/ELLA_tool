import threading
import os
import sys
import logging
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from flask import send_from_directory, request
from flask_restful import Api
from api import app, db
from api.v1 import ApiV1

# For /reset purposes
from vardb.deposit.deposit_testdata import DepositTestdata
from cli.commands.database import drop_db, make_db


SCRIPT_DIR = os.path.abspath(os.path.dirname(__file__))
STATIC_FILE_DIR = os.path.join(SCRIPT_DIR, '../webui/build')

log = app.logger


@app.before_first_request
def setup_logging():
    if not app.debug:
        log.addHandler(logging.StreamHandler())
        log.setLevel(logging.INFO)


@app.before_request
def before_request():
    if app.testing:  # don't add noise to console in tests, see tests.util.FlaskClientProxy
        return
    if request.method in ['PUT', 'POST', 'DELETE']:
        log.warning(" {method} - {endpoint} - {json}".format(
            method=request.method,
            endpoint=request.url,
            json=request.get_json()
            )
        )


@app.teardown_appcontext
def shutdown_session(exception=None):
    db.session.remove()


def serve_static(path=None):
    if not path:
        path = 'index.html'

    valid_files = [
        'app.css',
        'base.css',
        'app.js',
        'thirdparty.js',
        'templates.js',
        'fonts'
    ]

    if not any(v == path or path.startswith(v) for v in valid_files):
        path = 'index.html'

    return send_from_directory(STATIC_FILE_DIR, path)


# Only enabled on "DEVELOP=true"
def reset_testdata():
    if os.environ.get('DEVELOP', '').upper() != 'TRUE':
        raise RuntimeError("Tried to access reset resource, but not running in development mode")

    test_set = 'small'
    if request.args.get('testset'):
        test_set = request.args.get('testset')
    blocking = request.args.get('blocking')

    return do_testdata_reset(test_set, blocking=blocking)


def reset_testdata_from_cli():
    test_set = os.getenv('RESET_DB', 'small')
    do_testdata_reset(test_set)


def do_testdata_reset(test_set, blocking=True):
    def worker():
        drop_db.drop_db()
        make_db.make_db()

        dt = DepositTestdata(db)
        dt.deposit_all(test_set=test_set)

    if blocking:
        worker()
        return "Test database reset successfully."
    else:
        t = threading.Thread(target=worker)
        t.start()
        return "Test database is resetting. It should be ready in a minute."

api = Api(app)

# Setup resources for v1
ApiV1(app, api).setup_api()

if os.environ.get('SERVE_STATIC'):
    app.add_url_rule('/', 'index', serve_static)
    app.add_url_rule('/<path:path>', 'index_redirect', serve_static)

# This is used by development - production will not trigger it
if __name__ == '__main__':
    if os.getenv('RESET_DB', False):
        reset_testdata_from_cli()
        exit(0)
    opts = {}
    opts['host'] = '0.0.0.0'
    opts['threaded'] = True
    opts['port'] = int(os.getenv('API_PORT', '5000'))

    # Dev mode stuff
    is_dev = os.getenv('DEVELOP', '').lower() == 'true'
    if is_dev:
        opts['use_reloader'] = True
        app.add_url_rule('/reset', 'reset', reset_testdata)
        os.environ['ANALYSES_PATH'] = '/ella/src/vardb/testdata/analyses/small/'

    if is_dev:
        print "!!!!!DEVELOPMENT MODE!!!!!"

    app.run(**opts)
