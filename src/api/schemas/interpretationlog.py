from marshmallow import fields, Schema
from .users import UserSchema


class InterpretationLogSchema(Schema):
    class Meta:
        title = "InterpretationLog"
        description = "Represents one interpretation log item."
        fields = (
            "id",
            "date_created",
            "message",
            "warning_cleared",
            "review_comment",
            "user_id",
            "priority",
            "alleleassessment_id",
        )

    user = fields.Nested(UserSchema)
