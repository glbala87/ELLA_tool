from flask.ext.marshmallow import Marshmallow
from marshmallow import fields, Schema, post_load

from api import app
from vardb.datamodel import assessment

ma = Marshmallow(app)


class ReferenceAssessmentSchema(Schema):
    class Meta:
        fields = ('id',
                  'allele_id',
                  'reference_id',
                  'analysis_id',
                  'genepanel_name',
                  'genepanel_version',
                  'dateLastUpdate',
                  'dateSuperceeded',
                  'user_id',
                  'evaluation')

    user_id = fields.Integer(allow_none=True)  # Debug only
    dateSuperceeded = fields.DateTime(allow_none=True)
    dateLastUpdate = fields.DateTime(allow_none=True)
    # evaluation = fields.Field(required=True)

    @post_load
    def make_object(self, data):
        return assessment.ReferenceAssessment(**data)
