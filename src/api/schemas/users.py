from marshmallow import Schema


class UserSchema(Schema):
    class Meta:
        fields = ('id',
                  'username',
                  'firstName',
                  'lastName')
