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
                  'date_last_update',
                  'date_superceeded',
                  'allele_id',
                  'analysis_id',
                  'genepanel_name',
                  'genepanel_version',
                  'annotation_id',
                  'previous_assessment_id',
                  'user_id',
                  'user',
                  'classification',
                  'seconds_since_update',
                  'evaluation',
                  'referenceassessments')

    user_id = fields.Integer()
    user = fields.Nested(users.UserSchema)
    evaluation = fields.Field(required=False, default={})
    classification = fields.Field(required=True)
    date_last_update = fields.DateTime()
    date_superceeded = fields.DateTime(allow_none=True)
    referenceassessments = fields.Nested(referenceassessments.ReferenceAssessmentSchema, many=True, attribute='referenceassessments')
    seconds_since_update = fields.Method('get_seconds_since_created')

    def get_seconds_since_created(self, obj):
        return (datetime.datetime.now() - obj.date_last_update).total_seconds()

    @post_load
    def make_object(self, data):
        return assessment.AlleleAssessment(**data)
