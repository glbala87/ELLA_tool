from marshmallow import Schema


class FilterConfigSchema(Schema):
    class Meta:
        fields = ("id", "name", "filterconfig", "active", "requirements")
