from marshmallow import Schema


class AnnotationSchema(Schema):
    class Meta:
        fields = ("id", "annotations", "schema_version", "annotation_config_id", "date_superceeded")


class AnnotationConfigSchema(Schema):
    class Meta:
        fields = ("id", "view")
