from flask.ext.marshmallow import Marshmallow
from marshmallow import Schema, fields

from api import app
from api.schemas import users

ma = Marshmallow(app)


class AnalysisInterpretationSchema(Schema):
    class Meta:
        title = "AnalysisInterpretation"
        description = 'Represents one round of interpretation of an analysis'
        # Fields to expose
        fields = ('id',
                  'status',
                  'user_state',
                  'state',
                  'date_last_update',
                  'genepanel_name',
                  'genepanel_version',
                  'user_id',
                  'user')

    user = fields.Nested(users.UserSchema)
