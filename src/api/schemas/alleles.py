from flask.ext.marshmallow import Marshmallow
from marshmallow import fields, Schema, post_dump

from api import app
from api.util.annotationprocessor import AnnotationProcessor

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


class AlleleSchema(Schema):

    def __init__(self, genepanel=None):
        super(AlleleSchema, self).__init__()
        self.genepanel = genepanel

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

    annotation = fields.Nested(AnnotationSchema)
    genotype = fields.Nested(GenotypeSchema)

    @post_dump
    def convert_annotation(self, allele):
        """
        Converts the annotation to a more servable format.
        """
        allele['annotation']['annotations'] = AnnotationProcessor.process(allele, genotype=allele.get('genotype'), genepanel=self.genepanel)
