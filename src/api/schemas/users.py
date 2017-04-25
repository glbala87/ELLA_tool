from marshmallow import Schema, fields


class UserSchema(Schema):
    class Meta:
        fields = ('id',
                  'username',
                  'first_name',
                  'last_name',
                  'full_name',
                  'abbrev_name',
                  'active',
        )

    full_name = fields.Method('get_full_name')
    abbrev_name = fields.Method('get_abbreviated_name')

    def get_full_name(self, obj):
        return ' '.join([obj.first_name, obj.last_name])

    def get_abbreviated_name(self, obj):
        return u'{}. {}'.format(obj.first_name[:1], obj.last_name)
