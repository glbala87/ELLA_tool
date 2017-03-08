from flask.ext.marshmallow import Marshmallow
from marshmallow import fields, Schema, post_load

from api import app
from vardb.datamodel import assessment

ma = Marshmallow(app)


class ReferenceAssessmentSchema(Schema):
    class Meta:
        title = 'ReferenceAssessment'
        description = "Represents an assessment of one reference in context of one allele."
        fields = ('id',
                  'allele_id',
                  'reference_id',
                  'analysis_id',
                  'genepanel_name',
                  'genepanel_version',
                  'date_created',
                  'date_superceeded',
                  'user_id',
                  'evaluation')

    user_id = fields.Integer(allow_none=True)  # Debug only
    date_created = fields.DateTime()
    date_superceeded = fields.DateTime(allow_none=True)
    # evaluation = fields.Field(required=True)

    @post_load
    def make_object(self, data):
        return assessment.ReferenceAssessment(**data)


class ReferenceAssessmentInputSchema(Schema):
    class Meta:
        title = 'ReferenceAssessmentInput'
        description = "Data needed to create a reference assessment"
        fields = ('allele_id',
                  'reference_id',
                  'analysis_id',
                  'genepanel_name',
                  'genepanel_version',
                  'user_id',
                  'evaluation')

    user_id = fields.Integer(allow_none=True)  # Debug only
    date_superceeded = fields.DateTime(allow_none=True)
    evaluation = fields.Field(required=True)

