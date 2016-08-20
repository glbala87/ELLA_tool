from marshmallow import Schema


class AlleleSchema(Schema):

    def __init__(self, include_annotation=False):
        super(AlleleSchema, self).__init__()

        if include_annotation:
            self.Meta.fields.append('annotation')

    class Meta:
        fields = ['id',
                  'genome_reference',
                  'chromosome',
                  'start_position',
                  'open_end_position',
                  'change_from',
                  'change_to',
                  'change_type']
