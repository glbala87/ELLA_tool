from marshmallow import Schema


class CustomAnnotationSchema(Schema):
    class Meta:
        fields = ('id',
                  'allele_id',
                  'user_id',
                  'annotations',
                  'date_superceeded',
                  'date_created')
