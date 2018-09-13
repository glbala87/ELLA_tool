from flask.ext.marshmallow import Marshmallow
from marshmallow import fields, Schema, post_dump

from api import app
from api.schemas import users

ma = Marshmallow(app)


class AlleleInterpretationSnapshotSchema(Schema):
    class Meta:
        title = "AlleleInterpretationSnapshot"
        description = 'snapshot of a allele interpretation with context'
        # Fields to expose
        fields = ('id',
                  'date_created',
                  'allele_id',
                  'alleleinterpretation_id',
                  'annotation_id',
                  'customannotation_id',
                  'alleleassessment_id',
                  'presented_alleleassessment_id',
                  'allelereport_id',
                  'date_created',
                  'presented_allelereport_id')


class AlleleInterpretationSchema(Schema):

    class Meta:
        title = "AlleleInterpretation"
        description = 'Represents one round of interpretation of an allele'
        # Fields to expose
        fields = ('id',
                  'status',
                  'finalized',
                  'workflow_status',
                  'user_state',
                  'state',
                  'genepanel_name',
                  'genepanel_version',
                  'date_last_update',
                  'date_created',
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
                  'finalized',
                  'workflow_status',
                  'allele_id',
                  'genepanel_name',
                  'genepanel_version',
                  'date_last_update',
                  'user_id',
                  'user')

    user = fields.Nested(users.UserSchema)
