import pathlib
import subprocess
import uuid
from hashlib import sha256
from typing import Dict, Optional

from api import schemas
from api.config import config
from api.schemas.pydantic.v1 import validate_output
from api.schemas.pydantic.v1.resources import (
    AttachmentListResponse,
    AttachmentPostResponse,
    SendFileResponse,
)
from api.util.analysis_attachments import get_attachments
from api.util.util import authenticate, paginate, rest_filter
from api.v1.resource import LogRequestResource
from flask import request, send_file
from sqlalchemy.orm.session import Session
from vardb.datamodel import attachment, sample, user
from werkzeug import FileStorage


class AttachmentListResource(LogRequestResource):
    @authenticate()
    @validate_output(AttachmentListResponse, paginated=True)
    @paginate
    @rest_filter
    def get(self, session: Session, rest_filter: Optional[Dict], **kwargs):
        # has user, page, per_page in kwargs, but they're unused
        vals = self.list_query(
            session,
            attachment.Attachment,
            schemas.AttachmentSchema(strict=True),
            rest_filter=rest_filter,
        )
        return vals


class AttachmentResource(LogRequestResource):
    @authenticate()
    @validate_output(AttachmentPostResponse)
    def post(self, session: Session, user: user.User):
        file_obj: FileStorage = request.files["file"]
        file_obj.stream.seek(0)  # Make sure we read from the beginning

        # Create temporary file to write to
        tmp_folder = pathlib.Path(config["app"]["attachment_storage"], "tmp")
        tmp_folder.mkdir(parents=True, exist_ok=True)
        tmp_path = tmp_folder.joinpath(uuid.uuid4().hex)
        sha_hasher = sha256()
        size = 0

        # Read and write file in blocks of 64kb, and update hash
        with tmp_path.open("wb") as tmp_file:
            while True:
                s = file_obj.read(65536)
                if s == b"":
                    break
                size += len(s)
                tmp_file.write(s)
                sha_hasher.update(s)

        # Move file to attachment_storage/sha_val[:2]/sha_val
        sha_val = sha_hasher.hexdigest()
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

        return {"id": atchmt.id}

    @authenticate()
    @validate_output(SendFileResponse)
    def get(self, session: Session, attachment_id: int, **kwargs):
        atchmt = (
            session.query(attachment.Attachment)
            .filter(attachment.Attachment.id == attachment_id)
            .one()
        )
        atchmt_schema = schemas.AttachmentSchema(strict=True)

        return send_file(
            atchmt_schema.get_path(atchmt), as_attachment=True, attachment_filename=atchmt.filename
        )


class AnalysisAttachmentResource(LogRequestResource):
    @authenticate()
    @validate_output(SendFileResponse)
    def get(self, session: Session, analysis_id: int, index: int, **kwargs):
        aname = (
            session.query(sample.Analysis.name).filter(sample.Analysis.id == analysis_id).scalar()
        )
        attachment = get_attachments(aname)[index]

        return send_file(str(attachment), as_attachment=True, attachment_filename=attachment.name)
