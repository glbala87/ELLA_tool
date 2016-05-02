import threading
import os
import sys
import logging
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from flask import send_from_directory, request
from flask.ext.restful import Api
from api import app, db
from api.v1 import ApiV1
from vardb.deposit.deposit_testdata import DepositTestdata

SCRIPT_DIR = os.path.abspath(os.path.dirname(__file__))

PROD_STATIC_FILE_DIR = os.path.join(SCRIPT_DIR, '../webui/prod')
DEV_STATIC_FILE_DIR = os.path.join(SCRIPT_DIR, '../webui/dev')

log = app.logger


@app.before_first_request
def setup_logging():
    if not app.debug:
        log.addHandler(logging.StreamHandler())
        log.setLevel(logging.INFO)


@app.before_request
def before_request():
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


def serve_static_factory(dev=False):
    static_path = PROD_STATIC_FILE_DIR
    if dev:
        static_path = DEV_STATIC_FILE_DIR

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

        return send_from_directory(static_path,
                                   path)

    return serve_static


# Only enabled on "DEVELOP=true"
def reset_testdata():
    if os.environ.get('DEVELOP').upper() != 'TRUE':
        raise RuntimeError("Tried to access reset resource, but not running in development mode")

    test_set = 'small'
    if request.args.get('testset'):
        test_set = request.args.get('testset')

    def worker():
        dt = DepositTestdata(db)
        dt.deposit_all(test_set=test_set)

    t = threading.Thread(target=worker)
    t.start()

    return "Test database is resetting. It should be ready in a minute."


api = Api(app)

def init_v1(api):
    v1 = ApiV1()
    if os.environ.get('DEVELOP').upper() == 'TRUE':
        app.add_url_rule('/reset', 'reset', reset_testdata)
    return v1.init_app(api)

init_v1(api)

# This is used by development and medicloud - production will not trigger it
if __name__ == '__main__':
    opts = {}
    opts['host'] = '0.0.0.0'
    opts['threaded'] = True
    opts['port'] = int(os.getenv('API_PORT', '5000'))
    is_dev = os.getenv('DEVELOP', False)
    opts['debug'] = is_dev
    app.add_url_rule('/', 'index', serve_static_factory(dev=is_dev))
    app.add_url_rule('/<path:path>', 'index_redirect', serve_static_factory(dev=is_dev))
    app.run(**opts)
