from marshmallow import Schema, fields
from api.schemas.genepanels import GenepanelSchema


class UserSchema(Schema):
    class Meta:
        fields = ("id", "username", "first_name", "last_name", "full_name", "abbrev_name", "active")

    full_name = fields.Method("get_full_name")
    abbrev_name = fields.Method("get_abbreviated_name")

    def get_full_name(self, obj):
        return " ".join([obj.first_name, obj.last_name])

    def get_abbreviated_name(self, obj):
        return (
            " ".join([v[0] + "." for v in [obj.first_name] + obj.last_name.split()[:-1]])
            + " "
            + obj.last_name.split()[-1]
        )


class UserGroupSchema(Schema):
    class Meta:
        fields = ("id", "name", "genepanels", "default_import_genepanel")

    genepanels = fields.Nested(GenepanelSchema, many=True)
    default_import_genepanel = fields.Nested(GenepanelSchema, many=False)


class UserFullSchema(Schema):
    class Meta:
        fields = (
            "id",
            "username",
            "first_name",
            "last_name",
            "full_name",
            "email",
            "abbrev_name",
            "active",
            "password_expiry",
            "group",
        )

    full_name = fields.Method("get_full_name")
    abbrev_name = fields.Method("get_abbreviated_name")
    group = fields.Nested(UserGroupSchema)

    def get_full_name(self, obj):
        return " ".join([obj.first_name, obj.last_name])

    def get_abbreviated_name(self, obj):
        return (
            " ".join([v[0] + "." for v in [obj.first_name] + obj.last_name.split()[:-1]])
            + " "
            + obj.last_name.split()[-1]
        )
