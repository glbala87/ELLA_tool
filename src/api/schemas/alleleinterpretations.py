from flask.ext.marshmallow import Marshmallow
from marshmallow import fields, Schema

from api import app
from api.schemas import users

ma = Marshmallow(app)


class AlleleInterpretationSchema(Schema):
    class Meta:
        title = "AlleleInterpretation"
        description = 'Represents one round of interpretation of an allele'
        # Fields to expose
        fields = ('id',
                  'status',
                  'user_state',
                  'state',
                  'genepanel_name',
                  'genepanel_version',
                  'date_last_update',
                  'user_id',
                  'user')

    user = fields.Nested(users.UserSchema)
