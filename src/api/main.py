import os
from flask import send_from_directory
from flask.ext.restful import Api
from api import app, apiv1, session

SCRIPT_DIR = os.path.abspath(os.path.dirname(__file__))

STATIC_FILE_DIR = os.path.join(SCRIPT_DIR, '../webui/dest')


@app.teardown_appcontext
def shutdown_session(exception=None):
    session.remove()


@app.route('/<path:path>')
@app.route('/')
def download_file(path=None):
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

    return send_from_directory(STATIC_FILE_DIR,
                               path)


# Serve static


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
    # TODO: Note, flask dev server is not intended for production use, look into wsgi servers
    app.run(debug=True, threaded=True)
