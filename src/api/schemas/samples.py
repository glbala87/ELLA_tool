from marshmallow import fields, Schema


class SampleSchema(Schema):
    class Meta:
        title = "Sample"
        description = "Represents one sample. There can be many samples per analysis."
        fields = (
            "id",
            "identifier",
            "sample_type",
            "date_deposited",
            "affected",
            "proband",
            "family_id",
            "father_id",
            "mother_id",
            "sibling_id",
            "sex",
        )
