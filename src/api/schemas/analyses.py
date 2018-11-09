from marshmallow import fields, Schema

from api.schemas import analysisinterpretations, samples, genepanels


class UserSchema(Schema):
    class Meta:
        title = "User"
        description = 'User data'
        fields = ('id',
                  'username',
                  'first_name',
                  'last_name')


class AnalysisSchema(Schema):
    class Meta:
        title = "Analysis"
        description = 'Represents one analysis'
        fields = ('id',
                  'name',
                  'date_requested',
                  'date_deposited',
                  'interpretations',
                  'genepanel',
                  'samples',
                  'report',
                  'warnings')

    samples = fields.Nested(samples.SampleSchema, many=True)
    genepanel = fields.Nested(genepanels.GenepanelSchema)
    interpretations = fields.Nested(
        analysisinterpretations.AnalysisInterpretationOverviewSchema, many=True)
