from flask.ext.marshmallow import Marshmallow
from marshmallow import Schema

from api import app

ma = Marshmallow(app)


class ReferenceSchema(Schema):
    class Meta:
        fields = ('id',
                  'authors',
                  'title',
                  'journal',
                  'year',
                  'abstract',
                  'pubmed_id',
                  'published')
