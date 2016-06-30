from marshmallow import Schema


class UserSchema(Schema):
    class Meta:
        fields = ('id',
                  'username',
                  'first_name',
                  'last_name')
