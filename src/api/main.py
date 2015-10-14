import threading
import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
import argparse

from flask import send_from_directory
from flask.ext.restful import Api
from api import app, apiv1, session

from vardb.deposit.deposit_testdata import DepositTestdata

SCRIPT_DIR = os.path.abspath(os.path.dirname(__file__))

PROD_STATIC_FILE_DIR = os.path.join(SCRIPT_DIR, '../webui/prod')
DEV_STATIC_FILE_DIR = os.path.join(SCRIPT_DIR, '../webui/dev')


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
    def worker():
        dt = DepositTestdata()
        dt.deposit_all(small_only=True)

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
api.add_resource(apiv1.ReferenceResource, '/api/v1/references/')
api.add_resource(apiv1.ReferenceAssessmentResource, '/api/v1/referenceassessments/<int:ra_id>/')
api.add_resource(apiv1.ReferenceAssessmentListResource, '/api/v1/referenceassessments/')
api.add_resource(apiv1.UserListResource, '/api/v1/users/')
api.add_resource(apiv1.UserResource, '/api/v1/users/<username>/')
api.add_resource(apiv1.AlleleAssessmentResource, '/api/v1/alleleassessments/<int:aa_id>/')
api.add_resource(apiv1.AlleleAssessmentListResource, '/api/v1/alleleassessments/')


if __name__ == '__main__':

    parser = argparse.ArgumentParser(description='API server')
    parser.add_argument('--dev', required=False, action="store_true", help='Serves dev files instead of production', dest='dev')

    args = parser.parse_args()

    if args.dev:
        app.add_url_rule('/', 'index', serve_static_factory(dev=True))
        app.add_url_rule('/<path:path>', 'index_redirect', serve_static_factory(dev=True))
        app.run(debug=True, threaded=True)
    else:
        # TODO: Note, flask dev server is not intended for production use, look into wsgi servers
        port = os.getenv('VCAP_APP_PORT', '5000')
        app.add_url_rule('/', 'index', serve_static_factory())
        app.add_url_rule('/<path:path>', 'index_redirect', serve_static_factory())
        app.run(threaded=True,host='0.0.0.0', port=int(port))
