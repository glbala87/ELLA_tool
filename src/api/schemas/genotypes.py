from marshmallow import fields, Schema


class GenotypeSchema(Schema):
    class Meta:
        fields = ('id',
                  'genotypeQuality',
                  'sequencingDepth',
                  'variantQuality',
                  'alleleDepth',
                  'filterStatus',
                  'homozygous',
                  'genotype')

    genotype = fields.Method("get_genotype")

    def get_genotype(self, obj):

        if obj.secondallele:
            v1 = obj.allele.changeTo or '-'
            v2 = obj.secondallele.changeTo or '-'
        elif obj.homozygous:
            v1 = obj.allele.changeTo or '-'
            v2 = obj.allele.changeTo or '-'
        else:
            v1 = obj.allele.changeFrom or '-'
            v2 = obj.allele.changeTo or '-'
        return '{}/{}'.format(v1, v2)

