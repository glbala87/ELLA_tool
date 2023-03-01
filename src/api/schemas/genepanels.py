from marshmallow import Schema, fields


class GeneSchema(Schema):
    class Meta:
        title = "Gene"
        fields = ("hgnc_id", "hgnc_symbol")


class GeneFullSchema(Schema):
    class Meta:
        title = "Gene"
        fields = ("hgnc_id", "hgnc_symbol", "ensembl_gene_id", "omim_entry_id")


class TranscriptSchema(Schema):
    class Meta:
        title = "Transcript"
        fields = ("transcript_name", "gene")

    gene = fields.Nested(GeneSchema)


class TranscriptFullSchema(Schema):
    class Meta:
        title = "Transcript"
        fields = (
            "transcript_name",
            "genome_reference",
            "chromosome",
            "tx_start",
            "tx_end",
            "strand",
            "tags",
            "cds_start",
            "cds_end",
            "exon_starts",
            "exon_ends",
            "gene",
        )

    gene = fields.Nested(GeneFullSchema)


class PhenotypeSchema(Schema):
    class Meta:
        title = "Phenotype"
        fields = ("id", "gene", "inheritance")

    gene = fields.Nested(GeneSchema)


class PhenotypeFullSchema(Schema):
    class Meta:
        title = "Phenotype"
        fields = ("id", "description", "inheritance", "omim_id", "gene")

    gene = fields.Nested(GeneFullSchema)


class GenepanelFullSchema(Schema):
    class Meta:
        title = "Genepanel"
        description = "Panel of genes connected to a certain analysis"
        fields = ("name", "version", "transcripts", "phenotypes")

    transcripts = fields.Nested(TranscriptFullSchema, many=True)
    phenotypes = fields.Nested(PhenotypeFullSchema, many=True)


class GenepanelTranscriptsSchema(Schema):
    class Meta:
        title = "Genepanel"
        description = "Panel of genes connected to a certain analysis"
        fields = ("name", "version", "transcripts", "phenotypes")

    transcripts = fields.Nested(TranscriptSchema, many=True)
    phenotypes = fields.Nested(PhenotypeSchema, many=True)


class GenepanelSchema(Schema):
    class Meta:
        fields = ("name", "version", "official")


class InheritanceSchema(Schema):
    class Meta:
        fields = ("hgnc_id", "inheritance", "transcript_name")
