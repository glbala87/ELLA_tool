from marshmallow import Schema


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
                  'changeType')
