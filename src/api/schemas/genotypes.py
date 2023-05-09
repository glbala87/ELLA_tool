from marshmallow import Schema


class GenotypeSchema(Schema):
    class Meta:
        fields = ("id", "variant_quality", "filter_status")


class GenotypeSampleDataSchema(Schema):
    class Meta:
        fields = (
            "id",
            "type",
            "multiallelic",
            "genotype_quality",
            "genotype_likelihood",
            "sequencing_depth",
            "allele_depth",
            "copy_number",
        )
