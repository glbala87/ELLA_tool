from typing import Dict

from api import schemas
from api.polling import ANNOTATION_SERVICE_URL, AnnotationJobsInterface, AnnotationServiceInterface
from api.util.util import authenticate, logger, paginate, request_json, rest_filter
from api.v1.resource import LogRequestResource
from flask import request
from sqlalchemy.orm import Session
from vardb.datamodel import annotationjob, user


class AnnotationJobList(LogRequestResource):
    @authenticate()
    @rest_filter
    @paginate
    @logger(exclude=True)
    def get(self, session, rest_filter=None, page=None, per_page=None, user=None):
        """
        Lists annotation jobs in the system.

        ---
        summary: List annotation jobs
        tags:
            - Import
        """

        if rest_filter is None:
            rest_filter = dict()
        rest_filter[("genepanel_name", "genepanel_version")] = [
            (gp.name, gp.version) for gp in user.group.genepanels
        ]

        return self.list_query(
            session,
            annotationjob.AnnotationJob,
            schemas.AnnotationJobSchema(),
            rest_filter=rest_filter,
            order_by=annotationjob.AnnotationJob.date_submitted.desc(),
            page=page,
            per_page=per_page,
        )

    @authenticate()
    @request_json()
    def post(self, session: Session, data: Dict, user: user.User):
        """
        Creates an annotation job in the system.

        ---
        summary: Create annotation job
        tags:
            - Import
        """
        data["user_id"] = user.id
        annotation_job_data = annotationjob.AnnotationJob(**data)
        session.add(annotation_job_data)
        session.commit()
        return schemas.AnnotationJobSchema().dump(annotation_job_data).data


class AnnotationJob(LogRequestResource):
    @authenticate()
    @request_json(allowed_fields=["status", "message", "task_id"])
    def patch(self, session, id, data=None, user=None):
        """
        Updates an annotation job in the system.

        ---
        summary: Update annotation job
        tags:
            - Import
        """
        annotationjob_interface = AnnotationJobsInterface(session)
        job = annotationjob_interface.patch(
            id, status=data.get("status"), message=data.get("message"), task_id=data.get("task_id")
        )
        session.commit()
        return schemas.AnnotationJobSchema().dump(job).data, 200

    def delete(self, session, id):
        """
        Removes an annotation job in the system.

        ---
        summary: Remove annotation job
        tags:
            - Import
        """
        job = (
            session.query(annotationjob.AnnotationJob)
            .filter(annotationjob.AnnotationJob.id == id)
            .one()
        )
        session.delete(job)
        session.commit()
        return None, 200


class AnnotationServiceRunning(LogRequestResource):
    def get(self, session):
        """
        Checks status of annotation service.

        ---
        summary: Get annotation service status.
        tags:
            - Import
        """
        annotationservice_interface = AnnotationServiceInterface(ANNOTATION_SERVICE_URL, session)
        return annotationservice_interface.annotation_service_running()


class ImportSamples(LogRequestResource):
    def get(self, session):
        """
        Returns available samples from import service

        ---
        summary: Get samples from import service
        tags:
            - Import
        """
        search_term = request.args.get("term")
        limit = request.args.get("limit")
        annotationservice_interface = AnnotationServiceInterface(ANNOTATION_SERVICE_URL, session)
        return annotationservice_interface.search_samples(search_term, limit)
