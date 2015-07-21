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
                  'comment')

    user_id = fields.Integer(allow_none=True)  # Debug only

    def make_object(self, data):
        return assessment.AlleleAssessment(**data)

    @validates_schema(pass_original=True)
    def validate_data(self, data, org):
        for field in ['classification', 'status', 'comment']:
            if field not in org:
                raise ValidationError("Missing field: {}".format(field))
