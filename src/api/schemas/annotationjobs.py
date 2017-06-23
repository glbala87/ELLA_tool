from marshmallow import fields, Schema
from users import UserSchema

class AnnotationJobSchema(Schema):
    class Meta:
        title = "Annotation job"
        description = "Variants submitted to annotation service"
        fields = ('id',
                  'task_id',
                  'status',
                  'message',
                  'status_history',
                  'user_id',
                  'mode',
                  'vcf',
                  'date_submitted',
                  'date_last_update',
                  'user',
                  'properties',
                  'genepanel_name',
                  'genepanel_version')
        skip_missing = True

    user = fields.Nested(UserSchema)
