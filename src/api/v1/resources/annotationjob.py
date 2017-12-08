from api import schemas
from api.polling import AnnotationJobsInterface, AnnotationServiceInterface, ANNOTATION_SERVICE_URL
from api.util.util import request_json, rest_filter, authenticate, logger
from api.v1.resource import LogRequestResource
from vardb.datamodel import annotationjob


class AnnotationJob(LogRequestResource):

    @authenticate()
    @rest_filter
    @logger(exclude=True)
    def get(self, session, rest_filter=None, page=None, num_per_page=None, user=None):
        if rest_filter is None:
            rest_filter = dict()
        rest_filter[("genepanel_name", "genepanel_version")] = [(gp.name, gp.version) for gp in user.group.genepanels]
        val = self.list_query(session,
                              annotationjob.AnnotationJob,
                              schemas.AnnotationJobSchema(),
                              rest_filter=rest_filter)

        return val

    @authenticate()
    @request_json([], True)
    def post(self, session, data=None, user=None):
        annotation_job_data = annotationjob.AnnotationJob(**data)
        session.add(annotation_job_data)
        session.commit()
        return schemas.AnnotationJobSchema().dump(annotation_job_data).data

    @authenticate()
    @request_json(['id'], allowed=['status', 'message', 'task_id'])
    def patch(self, session, data=None, user=None):
        annotationjob_interface = AnnotationJobsInterface(session)
        job = annotationjob_interface.patch(data["id"],
                                      status=data.get("status"),
                                      message=data.get("message"),
                                      task_id=data.get("task_id"))
        session.commit()

        return job, 200


    def delete(self, session, id):
        job = session.query(annotationjob.AnnotationJob).filter(
            annotationjob.AnnotationJob.id == id
        ).one()
        session.delete(job)
        session.commit()
        return None, 200


class AnnotationServiceRunning(LogRequestResource):

    def get(self, session):
        annotationservice_interface = AnnotationServiceInterface(ANNOTATION_SERVICE_URL)
        return annotationservice_interface.annotation_service_running()
