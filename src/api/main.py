import threading
import os
import sys
import logging
import time
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from flask import send_from_directory, request, g
from flask_restful import Api
from api import app, db, AuthenticationError, ConflictError
from api.v1 import ApiV1
from api.util.util import populate_g_user, log_request

# For /reset purposes
from vardb.deposit.deposit_testdata import DepositTestdata, DEFAULT_TESTSET, AVAILABLE_TESTSETS
from cli.commands.database import drop_db, make_db

KEYWORD_DEVELOPER_MODE = 'DEVELOP'
SCRIPT_DIR = os.path.abspath(os.path.dirname(__file__))
STATIC_FILE_DIR = os.path.join(SCRIPT_DIR, '../webui/build')

log = app.logger

@app.before_first_request
def setup_logging():
    if not app.debug:
        log.addHandler(logging.StreamHandler())
        log.setLevel(logging.INFO)

@app.before_request
def populate_request():
    g.request_start_time = time.time() * 1000.0
    g.log_hide_payload = False
    g.log_hide_response = True  # We only store response for certain resources due to size concerns
    populate_g_user()

@app.after_request
def after_request(response):
    log_request(response.status_code, response)
    db.session.commit()
    return response

@app.teardown_request
def teardown_request(exc):
    if exc:
        if request.url.startswith('/reset'):  # DEVELOPMENT
            return None
        log_request(500)
        db.session.commit()


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
    if os.environ.get(KEYWORD_DEVELOPER_MODE, '').upper() != 'TRUE':
        raise RuntimeError("Access to the reset endpoint is only allowed when running in development mode." +
                           " Set variable " + KEYWORD_DEVELOPER_MODE)

    # use default if none is given:
    test_set = request.args.get('testset', DEFAULT_TESTSET)
    test_set = test_set if test_set else DEFAULT_TESTSET
    return do_testdata_reset(test_set, blocking=request.args.get('blocking'))


def reset_testdata_from_cli():
    test_set = os.getenv('RESET_DB', DEFAULT_TESTSET)
    do_testdata_reset(test_set)


def do_testdata_reset(test_set, blocking=True):
    def worker():
        drop_db.drop_db()
        make_db.make_db()

        dt = DepositTestdata(db)
        dt.deposit_all(test_set=test_set)

    if test_set not in AVAILABLE_TESTSETS:
        return "Unknown test set '{0}'. Please specify one of {1}".format(test_set, ", ".join(AVAILABLE_TESTSETS))

    if blocking:
        worker()
        return "Test database reset successfully."
    else:
        t = threading.Thread(target=worker)
        t.start()
        return "Test database is resetting using test set '{}'. It should be ready in a minute.".format(test_set)

class ApiErrorHandling(Api):
    def handle_error(self, e):
        if isinstance(e, (AuthenticationError, ConflictError)):
            return self.make_response(e.message, e.status_code)
        else:
            return super(ApiErrorHandling, self).handle_error(e)


api = ApiErrorHandling(app)

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
    is_dev = os.getenv(KEYWORD_DEVELOPER_MODE, '').lower() == 'true'
    if is_dev:
        opts['use_reloader'] = True
        app.add_url_rule('/reset', 'reset', reset_testdata)
        os.environ['ANALYSES_PATH'] = '/ella/src/vardb/testdata/analyses/small/'

    if is_dev:
        print "!!!!!DEVELOPMENT MODE!!!!!"

    app.run(**opts)
