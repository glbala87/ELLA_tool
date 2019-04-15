from marshmallow import Schema


class ReferenceSchema(Schema):
    class Meta:
        fields = ("id", "authors", "title", "journal", "year", "abstract", "pubmed_id", "published")
