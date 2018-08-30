from marshmallow import fields, Schema
from .users import UserSchema

class InterpretationLogSchema(Schema):
    class Meta:
        title = "InterpretationLog"
        description = 'Represents one interpretation log item.'
        fields = ('id',
                  'date_created',
                  'message',
                  'resolved',
                  'message',
                  'warning_cleared',
                  'user',
                  'priority')

    user = fields.Nested(UserSchema)
