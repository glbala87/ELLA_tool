import pathlib
import subprocess
import uuid
from api.v1.resource import LogRequestResource
from api.config import config
from flask import request, send_file
from hashlib import sha256
from vardb.datamodel import attachment
from api import schemas
from api.util.util import authenticate, rest_filter, paginate


class AttachmentListResource(LogRequestResource):
    @authenticate()
    @paginate
    @rest_filter
    def get(self, session, rest_filter=None, user=None, per_page=None, page=None):
        vals = self.list_query(
            session,
            attachment.Attachment,
            schemas.AttachmentSchema(strict=True),
            rest_filter=rest_filter,
            per_page=None,
            page=None,
        )
        return vals


class AttachmentResource(LogRequestResource):
    @authenticate()
    def post(self, session, user=None):
        file_obj = request.files["file"]
        file_obj.stream.seek(0)  # Make sure we read from the beginning

        # Create temporary file to write to
        tmp_folder = pathlib.Path(config["app"]["attachment_storage"], "tmp")
        tmp_folder.mkdir(parents=True, exist_ok=True)
        tmp_path = tmp_folder.joinpath(uuid.uuid4().hex)
        sha_val = sha256()
        size = 0

        # Read and write file in blocks of 64kb, and update hash
        with tmp_path.open("wb") as tmp_file:
            while True:
                s = file_obj.read(65536)
                if s == b"":
                    break
                size += len(s)
                tmp_file.write(s)
                sha_val.update(s)

        # Move file to attachment_storage/sha_val[:2]/sha_val
        sha_val = sha_val.hexdigest()
        folder = pathlib.Path(config["app"]["attachment_storage"], sha_val[:2])
        folder.mkdir(parents=True, exist_ok=True)
        path = folder.joinpath(sha_val)
        tmp_path.rename(path)

        # Try to create thumbnail
        thumbnail_path = path.with_suffix(".thumbnail")
        if not thumbnail_path.is_file():
            try:
                # Use imagemagick to convert image. Request a thumbnail with a width of 300.
                cmd = "convert {ifile}[0] -thumbnail 300 -gravity center -background white -quality 90 -extent 300x300 jpeg:{ofile}"
                subprocess.check_call(cmd.format(ifile=path, ofile=thumbnail_path), shell=True)
            except subprocess.CalledProcessError:
                pass

        # Create database object
        data = {
            "sha256": sha_val,
            "filename": file_obj.filename,
            "size": size,
            "extension": file_obj.filename.rsplit(".", 1)[-1] if "." in file_obj.filename else "",
            "mimetype": file_obj.content_type,
            "user_id": user.id,
        }

        atchmt = attachment.Attachment(**data)
        session.add(atchmt)
        session.commit()

        return {"id": atchmt.id}, 200

    @authenticate()
    def get(self, session, attachment_id, user=None):
        atchmt = (
            session.query(attachment.Attachment)
            .filter(attachment.Attachment.id == attachment_id)
            .one()
        )
        atchmt_schema = schemas.AttachmentSchema(strict=True)

        return send_file(
            atchmt_schema.get_path(atchmt), as_attachment=True, attachment_filename=atchmt.filename
        )
