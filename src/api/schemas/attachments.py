import os
import base64
from marshmallow import Schema, fields
from api.config import config


class AttachmentSchema(Schema):
    class Meta:
        fields = ('id',
                  'sha256',
                  'filename',
                  'size',
                  'date_created',
                  'mimetype',
                  'extension',
                  'thumbnail'
        )

    thumbnail = fields.Method('get_thumbnail')

    def get_path(self, obj):
        return os.path.join(config["app"]["attachment_storage"], obj.sha256[:2], obj.sha256)

    def get_thumbnail(self, obj):
        path = self.get_path(obj)+".thumbnail"
        if not os.path.isfile(path):
            return None
        else:
            with open(path, 'r') as f:
                data = f.read()
            data = base64.b64encode(data)
            return data
