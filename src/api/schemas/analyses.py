from marshmallow import fields, Schema
from api.schemas import analysisinterpretations, samples, genepanels
from api.util.analysis_attachments import get_attachments


class UserSchema(Schema):
    class Meta:
        title = "User"
        description = "User data"
        fields = ("id", "username", "first_name", "last_name")


class AnalysisSchema(Schema):
    class Meta:
        title = "Analysis"
        description = "Represents one analysis"
        fields = (
            "id",
            "name",
            "date_requested",
            "date_deposited",
            "interpretations",
            "genepanel",
            "samples",
            "report",
            "warnings",
            "attachments",
        )

    samples = fields.Nested(samples.SampleSchema, many=True)
    genepanel = fields.Nested(genepanels.GenepanelSchema)
    interpretations = fields.Nested(
        analysisinterpretations.AnalysisInterpretationOverviewSchema, many=True
    )
    attachments = fields.Method("get_attachment_from_obj")

    def get_attachment_from_obj(self, obj):
        return [f.name for f in get_attachments(obj.name)]
