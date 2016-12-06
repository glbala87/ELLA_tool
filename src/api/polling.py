from werkzeug.serving import is_running_from_reloader

import threading
import atexit
import time
import json
import urllib2

def response_ok(response):
    return 200 <= response.status_code < 400

ANNOTATION_JOBS_PATH = "/api/v1/annotationjobs/"
ANNOTATION_SERVICE_ANNOTATE_PATH = "/api/v1/annotationservice/annotate/"
ANNOTATION_SERVICE_STATUS_PATH = "/api/v1/annotationservice/status/"
ANNOTATION_SERVICE_PROCESS_PATH = "/api/v1/annotationservice/process/"
DEPOSIT_SERVICE_PATH = "/api/v1/annotationservice/deposit/"

def process_running(c):
    QUERY = urllib2.quote(json.dumps(dict(status="RUNNING")))
    response = c.get(ANNOTATION_JOBS_PATH + "?q="+QUERY)

    if response_ok(response):
        running_jobs = json.loads(response.get_data())
        print "RUNNING: "
        print running_jobs
        for job in running_jobs:
            id = job["id"]
            status = job["status"]
            task_id = job["task_id"]
            as_response = c.get(ANNOTATION_SERVICE_STATUS_PATH+str(task_id))
            if not response_ok(as_response):
                status = "FAILED (ANNOTATION)"
                message = as_response.get_data()
                print message
                exit()
            else:
                as_status = json.loads(as_response.get_data())[task_id]
                print "\n"*2
                print as_status
                print "\n" * 2
                if as_status == "FAILED":
                    status = "FAILED (ANNOTATION)"
                    print status
                    exit()
                elif as_status == "SUCCESS":
                    status = "ANNOTATED"
                message = ""

            if status != "RUNNING":
                yield dict(id=id, status=status, message=message)

def process_submitted(c):
    QUERY = urllib2.quote(json.dumps(dict(status="SUBMITTED")))
    response = c.get(ANNOTATION_JOBS_PATH+"?q="+QUERY)

    if response_ok(response):
        submitted_jobs = json.loads(response.get_data())
        # Post submitted jobs to annotation service
        print "SUBMITTED: "
        print submitted_jobs
        for job in submitted_jobs:
            id = job["id"]
            unannotated_vcf = job["vcf"]
            as_response = c.post(ANNOTATION_SERVICE_ANNOTATE_PATH, data=json.dumps(dict(vcf=unannotated_vcf)), content_type='application/json')
            print as_response
            if not response_ok(as_response):
                status = "FAILED (SUBMISSION)"
                print "hei"
                exit()
                message = as_response.get_data()
                task_id = ""
            else:
                status = "RUNNING"
                message = ""
                task_id = json.loads(as_response.get_data())["task_id"]

            # Update
            yield dict(id=id, task_id=task_id, status=status, message=message)


def process_annotated(c):
    QUERY = urllib2.quote(json.dumps(dict(status=["ANNOTATED", "FAILED (PROCESSING)", "FAILED (DEPOSIT)"])))
    response = c.get(ANNOTATION_JOBS_PATH + "?q="+QUERY)

    if response_ok(response):
        # Post submitted jobs to annotation service
        annotated_jobs = json.loads(response.get_data())
        # Deposit done jobs
        print "ANNOTATION SUCCESSFUL: "
        print annotated_jobs
        for job in annotated_jobs:
            id = job["id"]
            task_id = job["task_id"]
            print ANNOTATION_SERVICE_PROCESS_PATH+task_id
            as_response = c.get(ANNOTATION_SERVICE_PROCESS_PATH+task_id)
            if not response_ok(as_response):
                status = "FAILED (PROCESSING)"
                message = as_response.get_data()
            else:
                annotated_vcf = json.loads(as_response.get_data())["data"]
                data = dict(id=id, annotated_vcf=annotated_vcf)
                deposit_response = c.post(DEPOSIT_SERVICE_PATH, data=json.dumps(data), content_type='application/json')
                if not response_ok(deposit_response):
                    status = "FAILED (DEPOSIT)"
                    message = deposit_response.get_data()
                else:
                    status = "DONE"
                    message = ""

            yield dict(id=id, status=status, message=message)


def db_job_update(c, data):
    print json.dumps(data, indent=1)
    a = c.patch(ANNOTATION_JOBS_PATH, data=json.dumps(data), content_type='application/json')
    return a

def polling(app, event):
    errors = dict(
        submitted=dict(),
        running=dict(),
        annotated=dict()
    )
    debug = False
    while not event.is_set():
        with app.test_client() as c:
            # Get all newly submitted task
            try:
                for update in process_running(c):
                    db_job_update(c, update)
            except Exception as e:
                errors["running"].setdefault(e.message, 0)
                errors["running"][e.message] += 1
                if debug: raise e

            try:
                for update in process_submitted(c):
                    db_job_update(c, update)
            except Exception as e:
                errors["submitted"].setdefault(e.message, 0)
                errors["submitted"][e.message] += 1
                if debug: raise e

            try:
                for update in process_annotated(c):
                    db_job_update(c, update)
            except Exception as e:
                errors["annotated"].setdefault(e.message, 0)
                errors["annotated"][e.message] += 1
                if debug: raise e

        time.sleep(5)
        print json.dumps(errors, indent=1)
    print "Received exit signal"

def setup_polling(app):
    #Initiate
    if not is_running_from_reloader():
       event = threading.Event()
       threading.Thread(target=polling, args=(app, event)).start()
       atexit.register(event.set)
