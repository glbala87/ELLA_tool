from marshmallow import fields, Schema


class SampleSchema(Schema):
    class Meta:
        title = "Sample"
        description = 'Represents one sample. There can be many samples per analysis.'
        fields = ('id',
                  'identifier',
                  'sample_type',
                  'deposit_date',
                  'sample_config')


class UserSchema(Schema):
    class Meta:
        title = "User"
        description = 'User data'
        fields = ('id',
                  'username',
                  'first_name',
                  'last_name')


class GenepanelSchema(Schema):
    class Meta:
        title = "Genepanel"
        description = 'Panel of genes connected to a certain analysis'
        fields = ('name',
                  'version')


class AnalysisInterpretationSchema(Schema):
    class Meta:
        title = "AnalysisInterpretation"
        description = 'Represents one round of interpretation of an analysis'
        fields = ('id',
                  'status',
                  'date_last_update',
                  'user')

    user = fields.Nested(UserSchema)


class AnalysisSchema(Schema):
    class Meta:
        title = "Analysis"
        description = 'Represents one analysis'
        fields = ('id',
                  'name',
                  'deposit_date',
                  'interpretations',
                  'genepanel',
                  'properties',
                  'samples')

    samples = fields.Nested(SampleSchema, many=True)
    genepanel = fields.Nested(GenepanelSchema)
    interpretations = fields.Nested(AnalysisInterpretationSchema, many=True)
