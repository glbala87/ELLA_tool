import datetime
import json
import logging
import traceback

import time
import urllib.request
import urllib.error
import urllib.parse
from urllib.parse import urlencode
import os
import binascii
import subprocess
import tempfile
from os.path import join
from pathlib import Path
import pytz
from sqlalchemy.exc import OperationalError

from api.config import config
from api.util.genepanel_to_bed import genepanel_to_bed
from vardb.datamodel import annotationjob
from vardb.deposit.deposit_alleles import DepositAlleles
from vardb.deposit.deposit_analysis import DepositAnalysis
from vardb.deposit.analysis_config import AnalysisConfigData

log = logging.getLogger(__name__)


def run_preimport(job):
    preimport_script = config["import"].get("preimport_script")
    if preimport_script is None:
        return {"files": {}, "variables": {}}

    assert os.path.isfile(preimport_script)
    priority = job.properties.get("priority", 1) if job.properties else 1

    args = [
        "GENEPANEL_NAME=%s" % job.genepanel_name,
        "GENEPANEL_VERSION=%s" % job.genepanel_version,
        "SAMPLE_ID=%s" % job.sample_id,
        "USERGROUP=%s" % job.user.group.name,
        "PRIORITY=%d" % priority,
    ]

    cmd = " ".join(args + [preimport_script])
    output = subprocess.check_output(cmd, shell=True).decode()
    unparsed_data = json.loads(output)

    parsed_data = {}
    parsed_data["variables"] = {}
    parsed_data["variables"] = unparsed_data["variables"]

    parsed_data["files"] = {}
    for key, path in unparsed_data["files"].items():
        filename = os.path.basename(path)
        with open(path, "r") as f:
            contents = f.read()
        parsed_data["files"][key] = (filename, contents)
    return parsed_data


def encode_multipart_formdata(fields, files):
    LIMIT = "-" * 10 + binascii.hexlify(os.urandom(10)).decode()
    CRLF = "\r\n"
    L = []
    for (key, value) in fields.items():
        L.append("--" + LIMIT)
        L.append('Content-Disposition: form-data; name="%s"' % key)
        L.append("")
        if isinstance(value, str):
            if not value.startswith('"'):
                value = '"' + value
            if not value.endswith('"'):
                value = value + '"'
        value = str(value)
        L.append(value)
    for (key, (filename, value)) in files.items():
        L.append("--" + LIMIT)
        L.append('Content-Disposition: form-data; name="%s"; filename="%s"' % (key, filename))
        L.append("Content-Type: application/octet-stream")
        L.append("")
        L.append(value)
    L.append("--" + LIMIT + "--")
    L.append("")
    body = CRLF.join(L)
    content_type = "multipart/form-data; boundary=%s" % LIMIT
    return content_type, body


ANNOTATION_SERVICE_URL = config["app"]["annotation_service"]


def get_error_message(e):
    try:
        msg = json.loads(e.read().decode())["message"]
    except Exception:
        msg = "Unable to determine error"
    return msg


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
        return (
            self.session.query(annotationjob.AnnotationJob)
            .filter(annotationjob.AnnotationJob.id == id)
            .one()
        )

    def create(self, data):
        return annotationjob.AnnotationJob(**data)

    def patch(self, id, **kwargs):
        patched = False
        job = self.get_with_id(id)
        allowed_keys = ["status", "message", "task_id"]
        assert len(set(kwargs) - set(allowed_keys)) == 0, "Illegal values passed to patch: " + str(
            set(kwargs) - set(allowed_keys)
        )

        if kwargs.get("status") and kwargs["status"] != job.status:
            if "history" not in job.status_history:
                job.status_history["history"] = list()

            job.status_history["history"].insert(
                0, {"time": datetime.datetime.now(pytz.utc).isoformat(), "status": job.status}
            )
            patched = True

        for k, v in list(kwargs.items()):
            assert hasattr(job, k)
            if v is not None and getattr(job, k) != v:
                setattr(job, k, v)
                patched = True

        if patched:
            job.date_last_update = datetime.datetime.now(pytz.utc)
        return job

    def deposit(self, id, annotated_vcf):
        job = self.get_with_id(id)
        mode = job.mode
<<<<<<< HEAD
        with tempfile.TemporaryDirectory() as folder:
            vcf_file = Path(folder) / "{}.vcf".format(job.id)
            analysis_file = Path(folder) / "{}.analysis".format(job.id)
            with open(vcf_file, "w") as vcf, open(analysis_file, "w") as af:
                vcf.write(annotated_vcf)
                vcf.flush()

                gp_name = job.genepanel_name
                gp_version = job.genepanel_version

                if mode == "Analysis":
                    analysis_name = job.properties["analysis_name"]
                    append = job.properties["create_or_append"] != "Create"
                    if append:
                        analysis_name = job.properties["analysis_name"]
                    else:
                        analysis_name = "{}.{}_{}".format(analysis_name, gp_name, gp_version)

                    af_data = {
                        "name": analysis_name,
                        "genepanel_name": job.genepanel_name,
                        "genepanel_version": job.genepanel_version,
                        "priority": job.properties.get("priority", 1),
                        "data": [
                            {"vcf": str(vcf_file), "technology": job.properties["sample_type"]}
                        ],
                    }

                    json.dump(af_data, af)
                    af.flush()

                    acd = AnalysisConfigData(analysis_file)
                    da = DepositAnalysis(self.session)
                    da.import_vcf(acd, append=append)

                elif mode in ["Variants", "Single variant"]:
                    deposit = DepositAlleles(self.session)
                    deposit.import_vcf(str(vcf_file), gp_name, gp_version)
                else:
                    raise RuntimeError("Unknown mode: %s" % mode)
=======
        f = tempfile.NamedTemporaryFile()
        f.write(annotated_vcf)
        f.flush()
        # fd = StringIO()
        # fd.write(annotated_vcf)
        # fd.flush()
        # fd.seek(0)

        gp_name = job.genepanel_name
        gp_version = job.genepanel_version

        if mode == "Analysis":
            analysis_name = job.properties["analysis_name"]
            append = job.properties["create_or_append"] != "Create"
            if not append:
                analysis_name = "{}.{}_{}".format(analysis_name, gp_name, gp_version)

            with tempfile.TemporaryDirectory() as folder:
                vcf_file = Path(folder.name / "{}.vcf".format(job.id))
                with open(vcf_file, "w") as vcf:
                    vcf.write(annotated_vcf)

                af_data = {
                    "name": analysis_name,
                    "genepanel_name": job.genepanel_name,
                    "genepanel_version": job.genepanel_version,
                    "priority": job.properties.get("priority", 1),
                    "data": [{"vcf": vcf_file, "technology": job.properties["sample_type"]}],
                }

                analysis_file = Path(folder.name / "{}.analysis".format(job.id))
                with open(analysis_file, "w") as af:
                    json.dump(af_data, af)

                acd = AnalysisConfigData(analysis_file)
                da = DepositAnalysis(self.session)
                da.import_vcf(acd, append=append)

        elif mode in ["Variants", "Single variant"]:

            deposit = DepositAlleles(self.session)
            deposit.import_vcf(fd, gp_name, gp_version)
        else:
            f.close()
            raise RuntimeError("Unknown mode: %s" % mode)
        f.close()
>>>>>>> 45a571e7 ([vardb] Redesign of .analysis-files)

    def delete(self, job):
        self.session.delete(job)

    def add(self, data):
        self.session.add(data)

    def commit(self):
        self.session.commit()

    def rollback(self):
        self.session.rollback()


class AnnotationServiceInterface:
    def __init__(self, url, session):
        self.base = join(url, "api/v1")
        self.session = session

    def annotate(self, job):
        r = urllib.request.Request(
            join(self.base, "annotate"),
            data=json.dumps({"input": job.data}).encode(),
            headers={"Content-type": "application/json"},
        )
        k = urllib.request.urlopen(r)
        return json.loads(k.read().decode())

    def annotate_sample(self, job):
        regions = genepanel_to_bed(self.session, job.genepanel_name, job.genepanel_version)

        data = run_preimport(job)

        data["files"]["regions"] = ("regions.bed", regions)
        data["variables"]["sample_id"] = job.sample_id

        content_type, body = encode_multipart_formdata(data["variables"], data["files"])

        r = urllib.request.Request(
            join(self.base, "samples/annotate"),
            data=body.encode(),
            headers={"Content-type": content_type},
        )
        k = urllib.request.urlopen(r)
        return json.loads(k.read().decode())

    def process(self, task_id):
        k = urllib.request.urlopen(join(self.base, "process", task_id))
        return k.read().decode()

    def status(self, task_id=None):
        """Get status of task_id or all tasks"""
        if task_id:
            k = urllib.request.urlopen(join(self.base, "status", task_id))
        else:
            k = urllib.request.urlopen(join(self.base, "status"))
        resp = json.loads(k.read().decode())
        return resp

    def search_samples(self, search_term, limit):
        """Search for samples and return results"""
        d = {"q": {"name": str(search_term)}}
        if limit:
            d["limit"] = str(limit)
        q = urlencode(d)

        k = urllib.request.urlopen(join(self.base, "samples", "?" + q))
        resp = json.loads(k.read().decode())
        result = []
        for k, v in resp.items():
            v.update(name=k)
            result.append(v)

        return sorted(result, key=lambda x: x["name"])

    def annotation_service_running(self):
        try:
            urllib.request.urlopen(join(self.base, "status"))
            return {"running": True}, 200
        except (urllib.error.HTTPError, urllib.error.URLError):
            return {"running": False}, 200


def process_running(annotation_service, running_jobs):
    for job in running_jobs:
        id = job.id
        status = job.status
        task_id = job.task_id
        try:
            response = annotation_service.status(task_id)
            if not response["active"]:
                status = "ANNOTATED"
            message = ""
        except urllib.error.HTTPError as e:
            status = "FAILED (ANNOTATION)"
            message = get_error_message(e)

        yield id, {"task_id": task_id, "status": status, "message": message}


def process_submitted(annotation_service, submitted_jobs):
    for job in submitted_jobs:
        id = job.id
        # data = job.data
        # sample_name = job.sample_name
        try:
            if job.data is not None:
                resp = annotation_service.annotate(job)
            elif job.sample_id is not None:
                resp = annotation_service.annotate_sample(job)
            else:
                raise RuntimeError("data or sample_name must be specified to run annotation")
            status = "RUNNING"
            message = ""
            task_id = resp["task_id"]
        except Exception as e:
            status = "FAILED (SUBMISSION)"
            message = get_error_message(e)
            task_id = ""

        # Update
        yield id, {"task_id": task_id, "status": status, "message": message}


def process_annotated(annotation_service, annotation_jobs, annotated_jobs):
    for job in annotated_jobs:
        id = job.id
        task_id = job.task_id
        try:
            annotated_vcf = annotation_service.process(task_id)
            annotation_jobs.commit()
        except urllib.error.HTTPError as e:
            status = "FAILED (PROCESSING)"
            message = get_error_message(e)
            yield id, {"status": status, "message": message}
            continue
        if job.sample_id is not None and not config["import"]["automatic_deposit_with_sample_id"]:
            status = "DONE"
            message = "Analysis has not been automatically imported"
            yield id, {"status": status, "message": message}
            continue
        try:
            annotation_jobs.deposit(id, annotated_vcf)
            status = "DONE"
            message = ""
        except Exception as e:
            annotation_jobs.rollback()
            status = "FAILED (DEPOSIT)"
            message = e.__class__.__name__ + ": " + getattr(e, "message", str(e))

        yield id, {"status": status, "message": message}


def patch_annotation_job(annotation_jobs, id, updates):
    try:
        annotation_jobs.patch(id, **updates)
        annotation_jobs.commit()
    except Exception as e:
        log.error(
            "Failed patch of annotation job {id} ({update}): {error}".format(
                id=id, update=str(updates), error=getattr(e, "message", str(e))
            )
        )
        annotation_jobs.rollback()


def polling(session):
    annotation_jobs = AnnotationJobsInterface(session)
    annotation_service = AnnotationServiceInterface(ANNOTATION_SERVICE_URL, session)

    def loop(session):
        while True:
            try:
                session.connection()

                if not session.bind.table_names():
                    # Database is not populated
                    session.remove()
                    time.sleep(5)
                    continue

                # Process running
                running_jobs = annotation_jobs.get_with_status("RUNNING")
                for id, update in process_running(annotation_service, running_jobs):
                    patch_annotation_job(annotation_jobs, id, update)
                    log.info("Processed running job {} with data {}".format(id, str(update)))

                # Process submitted
                submitted_jobs = annotation_jobs.get_with_status("SUBMITTED")
                for id, update in process_submitted(annotation_service, submitted_jobs):
                    patch_annotation_job(annotation_jobs, id, update)
                    log.info("Processed submitted job {} with data {}".format(id, str(update)))

                # Process annotated
                annotated_jobs = annotation_jobs.get_with_status("ANNOTATED")
                for id, update in process_annotated(
                    annotation_service, annotation_jobs, annotated_jobs
                ):
                    patch_annotation_job(annotation_jobs, id, update)
                    log.info("Processed annotated job {} with data {}".format(id, str(update)))

                # Remove session to avoid a hanging session
                session.remove()
                time.sleep(5)
            except OperationalError as e:
                # Database is not alive
                log.warning("Failed to poll annotation jobs (%s)" % e.message)
                session.remove()
                time.sleep(5)
                continue

    try:
        loop(session)
    except Exception as e:
        session.remove()
        traceback.print_exc()
        raise e


if __name__ == "__main__":

    from applogger import setup_logger

    setup_logger()

    from vardb.datamodel import DB

    db = DB()
    db.connect()

    log.info("Starting polling worker")
    log.info("Using annotation service at: {}".format(ANNOTATION_SERVICE_URL))
    polling(db.session)
