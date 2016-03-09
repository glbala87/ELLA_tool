import datetime
from flask.ext.marshmallow import Marshmallow
from marshmallow import fields, Schema, validates_schema, ValidationError, post_load

from api import app
from vardb.datamodel import assessment
from api.schemas import users

ma = Marshmallow(app)


class AlleleAssessmentSchema(Schema):
    class Meta:
        fields = ('id',
                  'dateLastUpdate',
                  'dateSuperceeded',
                  'allele_id',
                  'analysis_id',
                  'genepanelName',
                  'genepanelVersion',
                  'transcript_id',
                  'annotation_id',
                  'previousAssessment_id',
                  'genepanelVersion',
                  'user_id',
                  'user',
                  'status',
                  'classification',
                  'secondsSinceUpdate',
                  'evaluation')

    user_id = fields.Integer()
    user = fields.Nested(users.UserSchema)
    dateLastUpdate = fields.DateTime()
    dateSuperceeded = fields.DateTime(allow_none=True)
    secondsSinceUpdate = fields.Method('get_seconds_since_created')
    status = fields.Integer()

    def get_seconds_since_created(self, obj):
        return (datetime.datetime.now() - obj.dateLastUpdate).total_seconds()

    @post_load
    def make_object(self, data):
        return assessment.AlleleAssessment(**data)

    @validates_schema(pass_original=True)
    def validate_data(self, data, org):
        for field in ['classification']:
            if field not in org:
                raise ValidationError("Missing field: {}".format(field))
