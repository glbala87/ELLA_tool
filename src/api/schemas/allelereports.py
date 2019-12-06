import datetime
import pytz
from marshmallow import fields, Schema, post_load

from vardb.datamodel import assessment
from api.schemas import users


class UsergroupSchema(Schema):
    class Meta:
        fields = ("id", "name")


class AlleleReportSchema(Schema):
    class Meta:
        title = "AlleleReport"
        description = "Represents a clinical report for one allele"
        fields = (
            "id",
            "date_created",
            "date_superceeded",
            "allele_id",
            "analysis_id",
            "previous_report_id",
            "user_id",
            "usergroup_id",
            "usergroup",
            "user",
            "seconds_since_update",
            "evaluation",
        )

    user_id = fields.Integer()
    user = fields.Nested(users.UserSchema)
    usergroup = fields.Nested(UsergroupSchema)
    evaluation = fields.Field(required=False, default={})
    date_created = fields.DateTime()
    date_superceeded = fields.DateTime(allow_none=True)
    seconds_since_update = fields.Method("get_seconds_since_created")

    def get_seconds_since_created(self, obj):
        return (datetime.datetime.now(pytz.utc) - obj.date_created).total_seconds()

    @post_load
    def make_object(self, data):
        return assessment.AlleleReport(**data)
