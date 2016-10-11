import datetime
from flask.ext.marshmallow import Marshmallow
from marshmallow import fields, Schema, validates_schema, ValidationError, post_load

from api import app
from vardb.datamodel import assessment
from api.schemas import users

ma = Marshmallow(app)


class AlleleReportSchema(Schema):
    class Meta:
        title = "AlleleReport"
        description = 'Represents a clinical report for one allele'
        fields = ('id',
                  'date_last_update',
                  'date_superceeded',
                  'allele_id',
                  'analysis_id',
                  'previous_report_id',
                  'user_id',
                  'user',
                  'seconds_since_update',
                  'evaluation')

    user_id = fields.Integer()
    user = fields.Nested(users.UserSchema)
    evaluation = fields.Field(required=False, default={})
    date_last_update = fields.DateTime()
    date_superceeded = fields.DateTime(allow_none=True)
    seconds_since_update = fields.Method('get_seconds_since_created')

    def get_seconds_since_created(self, obj):
        return (datetime.datetime.now() - obj.date_last_update).total_seconds()

    @post_load
    def make_object(self, data):
        return assessment.AlleleReport(**data)
