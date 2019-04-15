from marshmallow import Schema


class AlleleSchema(Schema):
    class Meta:
        fields = (
            "id",
            "genome_reference",
            "chromosome",
            "start_position",
            "open_end_position",
            "change_from",
            "change_to",
            "change_type",
            "vcf_pos",
            "vcf_ref",
            "vcf_alt",
        )
