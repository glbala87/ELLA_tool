from marshmallow import Schema, fields

from api.schemas import users


class AnalysisInterpretationSnapshotSchema(Schema):
    class Meta:
        title = "AnalysisInterpretationSnapshot"
        description = "snapshot of a allele interpretation with context"
        # Fields to expose
        fields = (
            "id",
            "date_created",
            "allele_id",
            "analysisinterpretation_id",
            "annotation_id",
            "customannotation_id",
            "alleleassessment_id",
            "presented_alleleassessment_id",
            "allelereport_id",
            "presented_allelereport_id",
        )


class AnalysisInterpretationSchema(Schema):
    class Meta:
        title = "AnalysisInterpretation"
        description = "Represents one round of interpretation of an analysis"
        # Fields to expose
        fields = (
            "id",
            "status",
            "finalized",
            "workflow_status",
            "user_state",
            "state",
            "date_last_update",
            "genepanel_name",
            "genepanel_version",
            "user_id",
            "user",
        )

    user = fields.Nested(users.UserSchema)


class AnalysisInterpretationOverviewSchema(Schema):
    class Meta:
        title = "AnalysisInterpretationOverview"
        description = (
            "Represents one round of interpretation of an analysis. Overview data fields only."
        )
        fields = (
            "id",
            "status",
            "analysis_id",
            "finalized",
            "workflow_status",
            "date_last_update",
            "genepanel_name",
            "genepanel_version",
            "user_id",
            "user",
        )

    user = fields.Nested(users.UserSchema)
