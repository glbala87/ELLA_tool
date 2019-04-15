from marshmallow import fields, Schema
from api.schemas.users import UserSchema


class AnnotationJobSchema(Schema):
    class Meta:
        title = "Annotation job"
        description = "Variants submitted to annotation service"
        fields = (
            "id",
            "task_id",
            "status",
            "message",
            "status_history",
            "user_id",
            "mode",
            "data",
            "sample_id",
            "date_submitted",
            "date_last_update",
            "user",
            "properties",
            "genepanel_name",
            "genepanel_version",
        )

    user = fields.Nested(UserSchema)
