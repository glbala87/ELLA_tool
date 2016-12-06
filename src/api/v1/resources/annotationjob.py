from api.util.util import request_json, rest_filter
import urllib2
from os.path import join
import json
from vardb.datamodel import sample

import datetime

from api.v1.resource import Resource
from api import schemas
from api.config import config

from vardb.deposit.deposit_analysis import DepositAnalysis

ANNOTATION_SERVICE = config["app"]["annotation_service"]

class AnnotationJob(Resource):
    @rest_filter
    def get(self, session, rest_filter=None, page=None, num_per_page=None):
        val = self.list_query(session,
                           sample.AnnotationJob,
                           schemas.AnnotationJobSchema(),
                           rest_filter=rest_filter)

        return val

    @request_json([], True)
    def post(self, session, data=None):
        annotation_job_data = sample.AnnotationJob(**data)
        session.add(annotation_job_data)
        session.commit()
        return schemas.AnnotationJobSchema().dump(annotation_job_data).data

    @request_json(['id'], allowed=['status', 'message', 'task_id'])
    def patch(self, session, data=None):
        id = data["id"]

        job = session.query(sample.AnnotationJob).filter(
            sample.AnnotationJob.id == id
        ).one()

        if data["status"] != job.status:
            if "history" not in job.status_history:
                job.status_history["history"] = list()

            job.status_history["history"].insert(0, {
                'time'    : datetime.datetime.now().isoformat(),
                'status'  : job.status,
            })

        for k,v in data.items():
            assert hasattr(job,k)
            if getattr(job,k) != v:
                setattr(job,k,v)

        job.date_last_update = datetime.datetime.now()
        session.commit()

        return None, 200

    def delete(self, session, id):
        job = session.query(sample.AnnotationJob).filter(
            sample.AnnotationJob.id == id
        ).one()
        session.delete(job)
        session.commit()
        return None, 200

class AnnotationJobDeposit(Resource):
    @request_json(["id", "annotated_vcf"])
    def post(self, session, data=None):
        # Deposit annoatated vcf
        id = data["id"]
        vcf = data["annotated_vcf"]

        job = session.query(sample.AnnotationJob).filter(
            sample.AnnotationJob.id == id
        ).one()

        mode = job.mode

        # TODO: Add support for file objects in VCFIterator
        from tempfile import NamedTemporaryFile
        tmpfile = NamedTemporaryFile(delete=False)
        tmpfile.write(vcf)
        tmpfile.close()

        filename = tmpfile.name
        from vardb.util.vcfiterator import VcfIterator

        if mode == "Analysis":
            type = job.properties["create_or_append"]
            assert type == "Create", "Only supports creating new analysis"
            analysis_name = job.properties["analysis_name"]
            deposit = DepositAnalysis(session)
            samples = VcfIterator(filename).getSamples()
            sample_config = [{"name": sname} for sname in samples]
            # vcf_sample_names = [analysis_name]
            genepanel = job.properties["genepanel"]
            # analysis_config = dict(params=dict(genepanel=genepanel))
            analysis_config = dict(
                params=dict(genepanel=genepanel),
                samples=samples,
                name = ".".join([analysis_name, genepanel])
            )
            deposit.import_vcf(filename,
                               sample_configs=sample_config,
                               analysis_config=analysis_config)
            session.commit()
        elif mode == "Variants":
            raise RuntimeError("Variant deposit not yet supported.")

class AnnotationServiceStatus(Resource):
    def get(self, session, task_id=None):
        "Get status of task_id or all tasks"
        if task_id:
            k = urllib2.urlopen(join(ANNOTATION_SERVICE, "status", task_id))
        else:
            k = urllib2.urlopen(join(ANNOTATION_SERVICE, "status"))
        resp = json.loads(k.read())
        return resp

class AnnotationServiceAnnotate(Resource):
    @request_json([], True)
    def post(self, session, data):
        "Post vcf, create job, return task_id"
        k = urllib2.urlopen(join(ANNOTATION_SERVICE, "annotate"), data=json.dumps(data))
        return json.loads(k.read())


class AnnotationServiceProcess(Resource):
    def get(self, session, task_id):
        "Return annotated vcf"
        k = urllib2.urlopen(join(ANNOTATION_SERVICE, "process", task_id))
        return json.loads(k.read())


