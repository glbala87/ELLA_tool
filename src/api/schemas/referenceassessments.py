from flask.ext.marshmallow import Marshmallow
from marshmallow import fields, Schema, validates_schema, ValidationError, post_load

from api import app
from vardb.datamodel import assessment

ma = Marshmallow(app)


class ReferenceAssessmentSchema(Schema):
    class Meta:
        fields = ('id',
                  'allele_id',
                  'reference_id',
                  'analysis_id',
                  'genepanelName',
                  'genepanelVersion',
                  'dateLastUpdate',
                  'user_id',
                  'evaluation')

    user_id = fields.Integer(allow_none=True)  # Debug only
    evaluation = fields.Field(required=True)

    @post_load
    def make_object(self, data):
        return assessment.ReferenceAssessment(**data)
