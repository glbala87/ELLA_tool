import datetime
import pytz
from marshmallow import fields, Schema, post_load

from vardb.datamodel import assessment
from api.schemas import users


class GeneAssessmentSchema(Schema):
    class Meta:
        title = "GeneAssessment"
        description = "Represents an assessment of one gene"
        fields = (
            "id",
            "date_created",
            "date_superceeded",
            "gene_id",
            "analysis_id",
            "previous_assessment_id",
            "user_id",
            "usergroup_id",
            "user",
            "seconds_since_update",
            "evaluation",
        )

    user_id = fields.Integer()
    user = fields.Nested(users.UserSchema)
    evaluation = fields.Field(required=False, default={})
    date_created = fields.DateTime()
    date_superceeded = fields.DateTime(allow_none=True)
    seconds_since_update = fields.Method("get_seconds_since_created")

    def get_seconds_since_created(self, obj):
        return (datetime.datetime.now(pytz.utc) - obj.date_created).total_seconds()

    @post_load
    def make_object(self, data):
        return assessment.AlleleAssessment(**data)
