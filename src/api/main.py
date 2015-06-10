import flask
from flask.ext.restful import Api

from api import app, apiv1, session


@app.teardown_appcontext
def shutdown_session(exception=None):
    session.remove()

"""
DEVELOPMENT ONLY!
"""
# TODO: Figure out how to deal with this in production.
@app.after_request
def add_cors(resp):
    """ Ensure all responses have the CORS headers. This ensures any failures are also accessible
        by the client. """
    resp.headers['Access-Control-Allow-Origin'] = flask.request.headers.get('Origin','*')
    resp.headers['Access-Control-Allow-Credentials'] = 'true'
    resp.headers['Access-Control-Allow-Methods'] = 'POST, OPTIONS, GET'
    resp.headers['Access-Control-Allow-Headers'] = flask.request.headers.get(
        'Access-Control-Request-Headers', 'Authorization' )
    # set low for debugging
    if app.debug:
        resp.headers['Access-Control-Max-Age'] = '1'
    return resp

api = Api(app)

api.add_resource(apiv1.AnalysisResource, '/api/v1/analyses/<int:id>')
api.add_resource(apiv1.AnalysisListResource, '/api/v1/analyses/')
api.add_resource(apiv1.SampleListResource, '/api/v1/samples/')
api.add_resource(apiv1.SampleInstanceResource, '/api/v1/samples/<string:sample_identifier>')
api.add_resource(apiv1.AlleleListResource, '/api/v1/alleles/')
api.add_resource(apiv1.ReferenceListResource, '/api/v1/references/')
api.add_resource(apiv1.AlleleResource, '/api/v1/alleles/<int:id>')


if __name__ == '__main__':
    app.run(debug=True)
