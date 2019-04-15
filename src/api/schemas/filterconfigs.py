from marshmallow import Schema, fields


class FilterConfigSchema(Schema):
    class Meta:
        fields = ("id", "name", "filterconfig", "active", "requirements")
