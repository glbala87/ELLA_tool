from marshmallow import Schema


class AnnotationSchema(Schema):
    class Meta:
        fields = ("id", "annotations", "date_superceeded")
