from flask.ext.marshmallow import Marshmallow
from marshmallow import fields, Schema

from api import app

ma = Marshmallow(app)


class AnnotationSchema(Schema):
    class Meta:
        fields = ('id',
                  'annotations',
                  'dateSuperceeded')


class GenotypeSchema(Schema):
    class Meta:
        fields = ('id',
                  'genotypeQuality',
                  'sequencingDepth',
                  'variantQuality',
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


class AlleleSchema(Schema):
    class Meta:
        fields = ('id',
                  'genomeReference',
                  'chromosome',
                  'startPosition',
                  'openEndPosition',
                  'changeFrom',
                  'changeTo',
                  'changeType',
                  'genotype',
                  'annotation')
        skip_missing = True

    annotation = fields.Nested(AnnotationSchema)
    genotype = fields.Nested(GenotypeSchema)

