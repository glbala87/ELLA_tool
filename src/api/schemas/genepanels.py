from marshmallow import fields, Schema


class GeneSchema(Schema):
    class Meta:
        title = 'Gene'
        fields = ('hugo_symbol',
                  'ensembl_gene_id',
                  'omim_entry_id')


class TranscriptSchema(Schema):
    class Meta:
        title = "Transcript"
        fields = ('refseq_name',
                  'ensembl_id',
                  'genome_reference',
                  'chromosome',
                  'tx_start',
                  'tx_end',
                  'strand',
                  'cds_start',
                  'cds_end',
                  'exon_starts',
                  'exon_ends',
                  'gene')

    gene = fields.Nested(GeneSchema)


class PhenotypeSchema(Schema):
    class Meta:
        title = "Phenotype"
        fields = ('id',
                  'genepanel_name',
                  'genepanel_version',
                  'description',
                  'inheritance',
                  'inheritance_info',
                  'omim_id',
                  'pmid',
                  'comment',
                  'gene')

    gene = fields.Nested(GeneSchema)


class GenepanelSchema(Schema):
    class Meta:
        title = "Genepanel"
        description = 'Panel of genes connected to a certain analysis'
        fields = ('name',
                  'version',
                  'transcripts',
                  'phenotypes',
                  'config')
    transcripts = fields.Nested(TranscriptSchema, many=True)
    phenotypes = fields.Nested(PhenotypeSchema, many=True)
