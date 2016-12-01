from flask.ext.marshmallow import Marshmallow
from marshmallow import fields, Schema

from api import app

ma = Marshmallow(app)

from .alleles import AlleleSchema


class AlleleInterpretationSchema(Schema):
    class Meta:
        title = "AlleleInterpretation"
        description = 'Represents one round of interpretation of an allele'
        # Fields to expose
        fields = ('id',
                  'status',
                  'user_state',
                  'state',
                  'date_last_update',
                  'allele',
                  'user_id')

    allele = fields.Nested(AlleleSchema)
