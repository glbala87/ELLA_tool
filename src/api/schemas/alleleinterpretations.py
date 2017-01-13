from flask.ext.marshmallow import Marshmallow
from marshmallow import fields, Schema, post_dump

from api import app
from api.schemas import users

ma = Marshmallow(app)


class AlleleInterpretationSchema(Schema):

    class Meta:
        title = "AlleleInterpretation"
        description = 'Represents one round of interpretation of an allele'
        # Fields to expose
        fields = ('id',
                  'status',
                  'user_state',
                  'state',
                  'genepanel_name',
                  'genepanel_version',
                  'date_last_update',
                  'user_id',
                  'user')

    user = fields.Nested(users.UserSchema)


class AlleleInterpretationOverviewSchema(Schema):

    class Meta:
        title = "AlleleInterpretationOverview"
        description = 'Represents one round of interpretation of an allele. Overview data fields only.'
        # Fields to expose
        fields = ('id',
                  'status',
                  'state',
                  'genepanel_name',
                  'genepanel_version',
                  'date_last_update',
                  'user_id',
                  'user')

    user = fields.Nested(users.UserSchema)

    @post_dump()
    def clean_state(self, data):
        """
        We only want to include the review_comment from state
        when included as part of analysis.
        """
        if 'review_comment' in data['state']:
            data['review_comment'] = data['state']['review_comment']
        del data['state']
