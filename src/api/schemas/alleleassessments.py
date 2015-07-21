import datetime
from flask.ext.marshmallow import Marshmallow
from marshmallow import fields, Schema, validates_schema, ValidationError

from api import app
from vardb.datamodel import assessment

ma = Marshmallow(app)


class AlleleAssessmentSchema(Schema):
    class Meta:
        fields = ('id',
                  'dateLastUpdate',
                  'dateSuperceeded',
                  'allele_id',
                  'interpretation_id',
                  'genepanelName',
                  'genepanelVersion',
                  'transcript_id',
                  'annotation_id',
                  'genepanelVersion',
                  'user_id',
                  'status',
                  'classification',
                  'daysSinceUpdate',
                  'evaluation')

    user_id = fields.Integer(allow_none=True)  # Debug only
    daysSinceUpdate = fields.Method('get_days_since_created')

    def get_days_since_created(self, obj):
        return (datetime.datetime.now() - obj.dateLastUpdate).days

    def make_object(self, data):
        return assessment.AlleleAssessment(**data)

    @validates_schema(pass_original=True)
    def validate_data(self, data, org):
        for field in ['classification', 'status', 'evaluation']:
            if field not in org:
                raise ValidationError("Missing field: {}".format(field))
