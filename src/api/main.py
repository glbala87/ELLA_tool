from flask.ext.restful import Api

from api import app, apiv1, session


@app.teardown_appcontext
def shutdown_session(exception=None):
    session.remove()

api = Api(app)

api.add_resource(apiv1.SampleListResource, '/api/v1/samples/')
api.add_resource(apiv1.SampleInstanceResource, '/api/v1/samples/<string:sample_identifier>')
api.add_resource(apiv1.AlleleListResource, '/api/v1/alleles/')
api.add_resource(apiv1.ReferenceListResource, '/api/v1/references/')
api.add_resource(apiv1.AlleleResource, '/api/v1/alleles/<int:id>')


if __name__ == '__main__':
    app.run(debug=True)
