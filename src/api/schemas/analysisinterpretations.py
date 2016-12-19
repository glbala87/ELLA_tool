from flask.ext.marshmallow import Marshmallow
from marshmallow import Schema

from api import app

ma = Marshmallow(app)


class AnalysisInterpretationSchema(Schema):
    class Meta:
        title = "AnalysisInterpretation"
        description = 'Represents one round of interpretation of an analysis'
        # Fields to expose
        fields = ('id',
                  'status',
                  'user_state',
                  'state',
                  'date_last_update',
                  'user_id')
