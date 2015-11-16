import threading
import os
import sys
import logging
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
import argparse

from flask import send_from_directory, request
from flask.ext.restful import Api
from api import app, apiv1, session

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
    session.remove()


def serve_static_factory(dev=False):
    static_path = PROD_STATIC_FILE_DIR
    if dev:
        static_path = DEV_STATIC_FILE_DIR

    def serve_static(path=None):
        if not path:
            path = 'index.html'

        valid_files = [
            'app.css',
            'app.js',
            'thirdparty.js',
            'fonts',
            'ngtmpl'
        ]

        if not any(v == path or path.startswith(v) for v in valid_files):
            path = 'index.html'

        return send_from_directory(static_path,
                                   path)

    return serve_static


# TODO: !!!!!!!!!!Remove before production!!!!!!!!!
@app.route('/reset')
def reset_testdata():
    small_only = not request.args.get('all') in ['True', 'true']

    def worker():
        dt = DepositTestdata()
        dt.deposit_all(small_only=small_only)

    t = threading.Thread(target=worker)
    t.start()

    return "Test database is resetting. It should be ready in a minute."


# Add API resources
api = Api(app)
api.add_resource(apiv1.AnalysisListResource, '/api/v1/analyses/')
api.add_resource(apiv1.InterpretationResource, '/api/v1/interpretations/<int:interpretation_id>/')
api.add_resource(apiv1.InterpretationAlleleResource, '/api/v1/interpretations/<int:interpretation_id>/alleles/')
api.add_resource(apiv1.InterpretationReferenceAssessmentResource, '/api/v1/interpretations/<int:interpretation_id>/referenceassessments/')
api.add_resource(apiv1.InterpretationActionCompleteResource, '/api/v1/interpretations/<int:interpretation_id>/actions/complete/')
api.add_resource(apiv1.InterpretationActionFinalizeResource, '/api/v1/interpretations/<int:interpretation_id>/actions/finalize/')
api.add_resource(apiv1.InterpretationActionOverrideResource, '/api/v1/interpretations/<int:interpretation_id>/actions/override/')
api.add_resource(apiv1.ReferenceResource, '/api/v1/references/')
api.add_resource(apiv1.ReferenceAssessmentResource, '/api/v1/referenceassessments/<int:ra_id>/')
api.add_resource(apiv1.ReferenceAssessmentListResource, '/api/v1/referenceassessments/')
api.add_resource(apiv1.UserListResource, '/api/v1/users/')
api.add_resource(apiv1.UserResource, '/api/v1/users/<int:user_id>/')
api.add_resource(apiv1.AlleleAssessmentResource, '/api/v1/alleleassessments/<int:aa_id>/')
api.add_resource(apiv1.AlleleAssessmentListResource, '/api/v1/alleleassessments/')
api.add_resource(apiv1.ACMGClassificationResource, '/api/v1/acmg/alleles/')

# This is used by development and medicloud - production will not trigger it
if __name__ == '__main__':
    opts = {}
    opts['host'] = '0.0.0.0'
    opts['threaded'] = True
    is_dev = os.getenv('DEVELOP', False)

    if is_dev:
        opts['debug'] = is_dev
    else:
        opts['port'] = int(os.getenv('VCAP_APP_PORT', '5000')) # medicloud bullshit
    app.add_url_rule('/', 'index', serve_static_factory(dev=is_dev))
    app.add_url_rule('/<path:path>', 'index_redirect', serve_static_factory(dev=is_dev))
    app.run(**opts)
