from marshmallow import fields, Schema


class SampleSchema(Schema):
    class Meta:
        fields = ('id',
                  'identifier',
                  'sampleType',
                  'deposit_date',
                  'sampleConfig')

class UserSchema(Schema):
    class Meta:
        fields = ('id',
                  'username',
                  'firstName',
                  'lastName')
        skip_missing = True


class GenepanelSchema(Schema):
    class Meta:
        fields = ('name',
                  'version')
        skip_missing = True


class AnalysisInterpretationSchema(Schema):
    class Meta:
        fields = ('id',
                  'status',
                  'dateLastUpdate',
                  'user')
        skip_missing = True

    user = fields.Nested(UserSchema)


class AnalysisSchema(Schema):
    class Meta:
        fields = ('id',
                  'name',
                  'deposit_date',
                  'interpretations',
                  'genepanel',
                  'samples')

    samples = fields.Nested(SampleSchema, many=True)
    genepanel = fields.Nested(GenepanelSchema)
    interpretations = fields.Nested(AnalysisInterpretationSchema, many=True)
