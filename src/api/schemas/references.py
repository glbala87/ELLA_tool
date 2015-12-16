from flask.ext.marshmallow import Marshmallow
from marshmallow import fields, Schema

from api import app

ma = Marshmallow(app)


class ReferenceSchema(Schema):
    class Meta:
        fields = ('id',
                  'authors',
                  'title',
                  'journal',
                  'year',
                  'URL',
                  'pubmedID')
