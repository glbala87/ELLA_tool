from marshmallow import fields, Schema


class SampleSchema(Schema):
    class Meta:
        title = "Sample"
        description = 'Represents one sample. There can be many samples per analysis.'
        fields = ('id',
                  'identifier',
                  'sample_type',
                  'proband',
                  'sex',
                  'family_id'
                  )
