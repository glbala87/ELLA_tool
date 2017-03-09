from api.util.util import request_json, rest_filter
import urllib2
from os.path import join
import json
import datetime
from api.polling import AnnotationJobsInterface, AnnotationServiceInterface, ANNOTATION_SERVICE_URL

from vardb.datamodel import annotationjob

from api.v1.resource import Resource
from api import schemas
from api.config import config


class AnnotationJob(Resource):
    @rest_filter
    def get(self, session, rest_filter=None, page=None, num_per_page=None):
        val = self.list_query(session,
                              annotationjob.AnnotationJob,
                              schemas.AnnotationJobSchema(),
                              rest_filter=rest_filter)

        return val

    @request_json([], True)
    def post(self, session, data=None):
        annotation_job_data = annotationjob.AnnotationJob(**data)
        session.add(annotation_job_data)
        session.commit()
        return schemas.AnnotationJobSchema().dump(annotation_job_data).data


    @request_json(['id'], allowed=['status', 'message', 'task_id'])
    def patch(self, session, data=None):
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

'''
class AnnotationJobDeposit(Resource):
    @request_json(["id", "annotated_vcf"])
    def post(self, session, data=None):
        # Deposit annoatated vcf
        id = data["id"]
        vcf = data["annotated_vcf"]

        job = session.query(annotationjob.AnnotationJob).filter(
            annotationjob.AnnotationJob.id == id
        ).one()

        mode = job.mode

        fd = StringIO()
        fd.write(str(vcf))
        fd.flush()
        fd.seek(0)

        from vardb.util.vcfiterator import VcfIterator
        samples = VcfIterator(fd).getSamples()
        sample_config = [{"name": sname} for sname in samples]
        genepanel = job.properties["genepanel"]

        if mode == "Analysis":
            type = job.properties["create_or_append"]
            if type == "Create":
                analysis_name = job.properties["analysis_name"]
                deposit = DepositAnalysis(session)
                analysis_config = {
                    "params": {"genepanel": genepanel},
                    "samples": samples,
                    "name": ".".join([analysis_name, genepanel])
                }
                deposit.import_vcf(fd,
                                   sample_configs=sample_config,
                                   analysis_config=analysis_config)
                session.commit()
            else:
                analysis_name = job.properties["analysis_name"]
                deposit = DepositAnalysisAppend(session)
                analysis_config = {
                    "params": {"genepanel": genepanel},
                    "samples": samples,
                    "name": analysis_name,
                }
                deposit.import_vcf(fd,
                                   sample_configs=sample_config,
                                   analysis_config=analysis_config)
                session.commit()
        elif mode == "Variants":
            deposit = DepositAlleles(session)
            allele_config = {
                "params": {"genepanel": genepanel},
                "samples": samples,
                "name": ".".join(["independent", genepanel])
            }

            try:
                deposit.import_vcf(fd,
                                   sample_configs=sample_config,
                                   allele_config=allele_config)
            except Exception as e:
                return e.message, 500
            session.commit()
'''

class AnnotationServiceRunning(Resource):
    def get(self, session):
        annotationservice_interface = AnnotationServiceInterface(ANNOTATION_SERVICE_URL)
        return annotationservice_interface.annotation_service_running()

'''
class AnnotationServiceStatus(Resource):
    def get(self, session, task_id=None):
        """Get status of task_id or all tasks"""
        if task_id:
            k = urllib2.urlopen(join(ANNOTATION_SERVICE, "status", task_id))
        else:
            k = urllib2.urlopen(join(ANNOTATION_SERVICE, "status"))
        resp = json.loads(k.read())
        return resp
'''
'''
class AnnotationServiceAnnotate(Resource):
    @request_json([], True)
    def post(self, session, data):
        """Post vcf, create job, return task_id"""
        k = urllib2.urlopen(join(ANNOTATION_SERVICE, "annotate"), data=json.dumps(data))
        return json.loads(k.read())
'''

'''
class AnnotationServiceProcess(Resource):
    def get(self, session, task_id):
        """Return annotated vcf"""
        k = urllib2.urlopen(join(ANNOTATION_SERVICE, "process", task_id))
        return json.loads(k.read())
'''