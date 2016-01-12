from marshmallow import Schema


class CustomAnnotationSchema(Schema):
    class Meta:
        fields = ('id',
                  'annotations',
                  'dateSuperceeded')
