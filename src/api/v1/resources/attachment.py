import os
import errno
import subprocess
from api.v1.resource import Resource
from api.config import config
from flask import request, send_file
from hashlib import sha256
from vardb.datamodel import attachment
from api import schemas
from api.util.util import request_json


# https://stackoverflow.com/questions/600268
def mkdir_p(path):
    try:
        os.makedirs(path)
    except OSError as exc:  # Python >2.5
        if exc.errno == errno.EEXIST and os.path.isdir(path):
            pass
        else:
            raise


class AttachmentResource(Resource):
    @authenticate()
    def post(self, session):
        file_obj = request.files["file"]
        file_obj.stream.seek(0)  # Make sure we read from the beginning
        content = file_obj.read()
        file_obj.stream.close()

        sha_val = sha256(content).hexdigest()
        existing = session.query(attachment.Attachment).filter(
            attachment.Attachment.sha256 == sha_val
        ).one_or_none()
        if existing is not None:
            return schemas.AttachmentSchema().dump(existing).data, 200

        folder = os.path.join(config["app"]["attachment_storage"], sha_val[:2])

        # Make sure folder structure exists
        mkdir_p(folder)

        # Write file to attachment storage
        path = os.path.join(folder, sha_val)
        with open(path, 'w') as f:
            f.write(content)

        # Try to create thumbnail
        try:
            cmd = "convert {ifile}[0] -thumbnail 10000@ -gravity center -background white -extent 100x100 jpeg:{ofile}"
            subprocess.check_call(cmd.format(ifile=path, ofile=path + ".thumbnail"), shell=True)
        except subprocess.CalledProcessError, e:
            pass


        data = {
            "sha256": sha_val,
            "filename": file_obj.filename,
            "size": len(content),
            "extension": file_obj.filename.rsplit('.',1)[-1],
            "mimetype": file_obj.content_type
        }

        atchmt = attachment.Attachment(**data)
        session.add(atchmt)
        session.commit()

        return schemas.AttachmentSchema().dump(atchmt).data, 200

    @authenticate()
    def get(self, session, attachment_id):
        atchmt = session.query(attachment.Attachment).filter(
            attachment.Attachment.id == attachment_id
        ).one()
        atchmt_schema = schemas.AttachmentSchema(strict=True)

        return send_file(atchmt_schema.get_path(atchmt), as_attachment=True, attachment_filename=atchmt.filename)



class AlleleAssessmentAttachmentResource(Resource):
    @authenticate()
    @request_json(["attachment_id", "alleleassessment_id"])
    def post(self, session, data):
        obj = attachment.AlleleAssessment(**data)
        session.add(obj)
        session.commit()
        return None, 200
