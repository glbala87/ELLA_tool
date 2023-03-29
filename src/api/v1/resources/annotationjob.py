from typing import Dict, Optional

from api import schemas
from api.polling import ANNOTATION_SERVICE_URL, AnnotationJobsInterface, AnnotationServiceInterface
from api.schemas.pydantic.v1 import validate_output
from api.schemas.pydantic.v1.resources import (
    AnnotationJobListResponse,
    AnnotationJobResponse,
    AnnotationSampleListResponse,
    AnnotationServiceStatusResponse,
    CreateAnnotationJobRequest,
    EmptyResponse,
    PatchAnnotationJobRequest,
)
from api.util.util import authenticate, logger, paginate, request_json, rest_filter
from api.v1.resource import LogRequestResource
from flask import request
from sqlalchemy.orm import Session
from vardb.datamodel import annotationjob, user


class AnnotationJobList(LogRequestResource):
    @authenticate()
    @validate_output(AnnotationJobListResponse, paginated=True)
    @rest_filter
    @paginate
    @logger(exclude=True)
    def get(
        self,
        session: Session,
        rest_filter: Optional[Dict],
        page: int,
        per_page: int,
        user: user.User,
        **kwargs
    ):
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
    @validate_output(AnnotationJobResponse)
    @request_json(model=CreateAnnotationJobRequest)
    def post(self, session: Session, data: CreateAnnotationJobRequest, user: user.User):
        """
        Creates an annotation job in the system.

        ---
        summary: Create annotation job
        tags:
            - Import
        """
        # data["user_id"] = user.id
        annotation_job_data = annotationjob.AnnotationJob(
            **{**data.dump(exclude_none=True), "user_id": user.id}
        )
        session.add(annotation_job_data)
        session.commit()
        return schemas.AnnotationJobSchema().dump(annotation_job_data).data


class AnnotationJob(LogRequestResource):
    @authenticate()
    @validate_output(AnnotationJobResponse)
    @request_json(model=PatchAnnotationJobRequest)
    def patch(self, session: Session, id: int, data: PatchAnnotationJobRequest, **kwargs):
        """
        Updates an annotation job in the system.

        ---
        summary: Update annotation job
        tags:
            - Import
        """
        annotationjob_interface = AnnotationJobsInterface(session)
        job = annotationjob_interface.patch(
            id, status=data.status, message=data.message, task_id=data.task_id
        )
        session.commit()
        return schemas.AnnotationJobSchema().dump(job).data

    @authenticate()
    @validate_output(EmptyResponse)
    def delete(self, session: Session, id: int):
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


class AnnotationServiceRunning(LogRequestResource):
    @validate_output(AnnotationServiceStatusResponse)
    def get(self, session: Session):
        """
        Checks status of annotation service.

        ---
        summary: Get annotation service status.
        tags:
            - Import
        """
        annotationservice_interface = AnnotationServiceInterface(ANNOTATION_SERVICE_URL, session)
        return {"running": annotationservice_interface.annotation_service_running()}


class ImportSamples(LogRequestResource):
    @validate_output(AnnotationSampleListResponse)
    def get(self, session: Session):
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
