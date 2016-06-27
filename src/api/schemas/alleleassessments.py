import datetime
from flask.ext.marshmallow import Marshmallow
from marshmallow import fields, Schema, validates_schema, ValidationError, post_load

from api import app
from vardb.datamodel import assessment
from api.schemas import users, referenceassessments

ma = Marshmallow(app)


class AlleleAssessmentSchema(Schema):
    class Meta:
        fields = ('id',
                  'dateLastUpdate',
                  'dateSuperceeded',
                  'allele_id',
                  'analysis_id',
                  'genepanel_name',
                  'genepanel_version',
                  'annotation_id',
                  'previousAssessment_id',
                  'user_id',
                  'user',
                  'classification',
                  'secondsSinceUpdate',
                  'evaluation',
                  'referenceassessments')

    user_id = fields.Integer()
    user = fields.Nested(users.UserSchema)
    evaluation = fields.Field(required=False, default=dict)
    classification = fields.Field(required=True)
    dateLastUpdate = fields.DateTime()
    dateSuperceeded = fields.DateTime(allow_none=True)
    referenceassessments = fields.Nested(referenceassessments.ReferenceAssessmentSchema, many=True, attribute='referenceAssessments')
    secondsSinceUpdate = fields.Method('get_seconds_since_created')

    def get_seconds_since_created(self, obj):
        return (datetime.datetime.now() - obj.dateLastUpdate).total_seconds()

    @post_load
    def make_object(self, data):
        return assessment.AlleleAssessment(**data)
