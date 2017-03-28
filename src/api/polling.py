import datetime
import json
import logging

import time
import urllib2
from StringIO import StringIO
from os.path import join
from sqlalchemy.exc import OperationalError

from api.config import config
from vardb.datamodel import annotationjob
from vardb.deposit.deposit_alleles import DepositAlleles
from vardb.deposit.deposit_analysis import DepositAnalysis
from vardb.deposit.deposit_analysis_append import DepositAnalysisAppend

# Make StringIO objects work fine in with-statements
StringIO.__exit__ = lambda *args: args[0]
StringIO.__enter__ = lambda *args: args[0]

log = logging.getLogger(__name__)

ANNOTATION_SERVICE_URL = config["app"]["annotation_service"]


class AnnotationJobsInterface:
    def __init__(self, session):
        self.session = session

    def get_all(self):
        query = self.session.query(annotationjob.AnnotationJob)
        return query.all()

    def get_with_status(self, status):
        if isinstance(status, str):
            status = [status]
        assert isinstance(status, (tuple, list))
        return self.session.query(annotationjob.AnnotationJob).filter(
            annotationjob.AnnotationJob.status.in_(status)
        )

    def get_with_id(self, id):
        return self.session.query(annotationjob.AnnotationJob).filter(
            annotationjob.AnnotationJob.id == id
        ).one()

    def create(self, data):
        return annotationjob.AnnotationJob(**data)

    def patch(self, id, **kwargs):
        job = self.get_with_id(id)
        allowed_keys = ["status", "message", "task_id"]
        assert len(set(kwargs) - set(allowed_keys)) == 0, "Illegal values passed to patch: " + str(
            set(kwargs) - set(allowed_keys))

        if kwargs.get("status") and kwargs["status"] != job.status:
            if "history" not in job.status_history:
                job.status_history["history"] = list()

            job.status_history["history"].insert(0, {
                'time': datetime.datetime.now().isoformat(),
                'status': job.status,
            })

        for k, v in kwargs.items():
            assert hasattr(job, k)
            if v is not None and getattr(job, k) != v:
                setattr(job, k, v)

        job.date_last_update = datetime.datetime.now()
        return job

    def deposit(self, id, annotated_vcf):
        job = self.get_with_id(id)
        mode = job.mode

        fd = StringIO()
        fd.write(str(annotated_vcf))
        fd.flush()
        fd.seek(0)

        genepanel = job.properties["genepanel"]
        gp_name, gp_version = job.properties["genepanel"].split('_', 1)

        if mode == "Analysis":
            type = job.properties["create_or_append"]
            if type == "Create":
                analysis_name = job.properties["analysis_name"]
                deposit = DepositAnalysis(self.session)
                deposit.import_vcf(fd,
                                   ".".join([analysis_name, genepanel]),
                                   gp_name,
                                   gp_version)
            else:
                analysis_name = job.properties["analysis_name"]
                deposit = DepositAnalysisAppend(self.session)
                deposit.import_vcf(fd,
                                   analysis_name,
                                   gp_name,
                                   gp_version)
        elif mode == "Variants":
            deposit = DepositAlleles(self.session)
            deposit.import_vcf(fd,
                               gp_name,
                               gp_version)

    def delete(self, job):
        self.session.delete(job)

    def add(self, data):
        self.session.add(data)

    def commit(self):
        self.session.commit()


class AnnotationServiceInterface:
    def __init__(self, url):
        self.url = url

    def annotate(self, unannotated_vcf):
        k = urllib2.urlopen(join(self.url, "annotate"), data=json.dumps({"vcf": unannotated_vcf}))
        return json.loads(k.read())

    def process(self, task_id):
        k = urllib2.urlopen(join(self.url, "process", task_id))
        return json.loads(k.read())

    def status(self, task_id=None):
        """Get status of task_id or all tasks"""
        if task_id:
            k = urllib2.urlopen(join(self.url, "status", task_id))
        else:
            k = urllib2.urlopen(join(self.url, "status"))
        resp = json.loads(k.read())
        return resp

    def annotation_service_running(self):
        try:
            k = urllib2.urlopen(join(self.url, "status"))
            return {"running": True}, 200
        except urllib2.HTTPError:
            return {"running": False}, 200


def process_running(annotation_service, running_jobs):
    for job in running_jobs:
        id = job.id
        status = job.status
        task_id = job.task_id
        try:
            response = annotation_service.status(task_id)
            if response[task_id] == "FAILED":
                status = "FAILED (ANNOTATION)"
            elif response[task_id] == "SUCCESS":
                status = "ANNOTATED"
            message = ""
        except urllib2.HTTPError, e:
            status = "FAILED (ANNOTATION)"
            message = e.message

        yield id, {"task_id": task_id, "status": status, "message": message}


def process_submitted(annotation_service, submitted_jobs):
    for job in submitted_jobs:
        id = job.id
        unannotated_vcf = job.vcf

        try:
            resp = annotation_service.annotate(unannotated_vcf)
            status = "RUNNING"
            message = ""
            task_id = resp["task_id"]
        except urllib2.HTTPError, e:
            status = "FAILED (SUBMISSION)"
            message = e.message
            task_id = ""

        # Update
        yield id, {"task_id": task_id, "status": status, "message": message}


def process_annotated(annotation_service, annotation_jobs, annotated_jobs):
    for job in annotated_jobs:
        id = job.id
        task_id = job.task_id
        try:
            resp = annotation_service.process(task_id)
        except urllib2.HTTPError, e:
            status = "FAILED (PROCESSING)"
            message = e.message
            yield {"id": id, "status": status, "message": message}
            continue

        annotated_vcf = resp["data"]

        try:
            annotation_jobs.deposit(id, annotated_vcf)
            status = "DONE"
            message = ""
        except Exception, e:
            status = "FAILED (DEPOSIT)"
            message = e.message

        yield id, {"status": status, "message": message}


def polling(session):
    annotation_jobs = AnnotationJobsInterface(session)
    annotation_service = AnnotationServiceInterface(ANNOTATION_SERVICE_URL)

    def loop(session):
        while True:
            try:
                session.connection()

                if len(session.bind.table_names()) == 0:
                    # Database is not populated
                    session.remove()
                    time.sleep(5)
                    continue

                # Process running
                running_jobs = annotation_jobs.get_with_status("RUNNING")
                for id, update in process_running(annotation_service, running_jobs):
                    annotation_jobs.patch(id, **update)
                annotation_jobs.commit()

                # Process submitted
                submitted_jobs = annotation_jobs.get_with_status("SUBMITTED")
                for id, update in process_submitted(annotation_service, submitted_jobs):
                    annotation_jobs.patch(id, **update)
                annotation_jobs.commit()

                # Process annotated
                annotated_jobs = annotation_jobs.get_with_status(["ANNOTATED", "FAILED (PROCESSING)", "FAILED (DEPOSIT)"])
                for id, update in process_annotated(annotation_service, annotation_jobs, annotated_jobs):
                    annotation_jobs.patch(id, **update)
                annotation_jobs.commit()

                # Remove session to avoid a hanging session
                session.remove()
                time.sleep(5)
            except OperationalError, e:
                # Database is not alive
                log.warning("Failed to poll annotation jobs (%s)" % e.message)
                session.remove()
                time.sleep(5)
                continue

    try:
        loop(session)
    except Exception, e:
        session.remove()
        raise e


if __name__ == '__main__':

    logging.basicConfig(level=logging.INFO)
    from vardb.datamodel import DB

    db = DB()
    db.connect()

    log.info("Starting polling worker")
    log.info("Using annotation service at: {}".format(ANNOTATION_SERVICE_URL))
    polling(db.session)
