import flask
from flask.ext.restful import Api
from flask.ext.cors import CORS
from api import app, apiv1, session


@app.teardown_appcontext
def shutdown_session(exception=None):
    session.remove()


api = Api(app)

"""
DEVELOPMENT ONLY!
TODO: Figure out how to do this properly.
"""
cors = CORS(app, resources={r"/api/*": {"origins": "*"}})

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
