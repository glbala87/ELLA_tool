from flask.ext.marshmallow import Marshmallow
from marshmallow import fields, Schema

from api import app

ma = Marshmallow(app)


class GenepanelSchema(Schema):
    class Meta:
        fields = ('name',
                  'version')
        skip_missing = True


class AnalysisInterpretationSchema(Schema):
    class Meta:
        fields = ('id',
                  'status',
                  'dateLastUpdate')
        skip_missing = True


class AnalysisSchema(Schema):
    class Meta:
        fields = ('id',
                  'name',
                  'interpretations',
                  'genepanel')

    genepanel = fields.Nested(GenepanelSchema)
    interpretations = fields.Nested(AnalysisInterpretationSchema, many=True)
