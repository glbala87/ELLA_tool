"""Testing is done by using a dummy annotation server.
This server is specified in ./annotationserver.py
and started in fixture"""
import pytest
import re
import socket
import urllib
import time
import multiprocessing
from .annotationserver import app
from api.polling import AnnotationJobsInterface, AnnotationServiceInterface, ANNOTATION_SERVICE_URL
from api.polling import process_annotated, process_submitted, process_running

ANNOTATION_JOBS_PATH = "/api/v1/import/service/jobs/"


@pytest.yield_fixture(scope="module", autouse=True)
def annotationserver():
    "Launch dummy annotation server in subprocess"
    host = re.findall("//([^:]*)", ANNOTATION_SERVICE_URL)[0]
    assert socket.gethostbyname(host) == socket.gethostbyname("localhost")
    port = int(re.findall(r":(\d+)", ANNOTATION_SERVICE_URL)[0])

    p = multiprocessing.Process(target=app.run, kwargs={"port": port, "host": host})
    p.start()
    max_retries = 10
    n = 0
    while True:
        try:
            urllib.request.urlopen(f"http://0.0.0.0:{port}")
            break
        except:
            time.sleep(0.5)
            n += 1
        if n >= max_retries:
            raise RuntimeError()

    yield
    p.terminate()


def test_annotationserver_running(client):
    response = client.get("/api/v1/import/service/running/")
    assert response.status_code == 200
    assert response.get_json()["running"]


def test_polling(session, client, test_database):
    # Submit to database
    data = dict(
        mode="Analysis",
        user_id=1,
        data="Dummy vcf data for testing",
        genepanel_name="HBOC",
        genepanel_version="v01.0",
        properties=dict(analysis_name="abc", create_or_append="Create", sample_type="HTS"),
    )

    response = client.post(ANNOTATION_JOBS_PATH, data=data)
    assert response.status_code == 200

    annotationjob_interface = AnnotationJobsInterface(session)
    annotationservice_interface = AnnotationServiceInterface(ANNOTATION_SERVICE_URL, session)

    # Process submitted
    submitted = annotationjob_interface.get_with_status("SUBMITTED")
    updates_submitted = list(process_submitted(annotationservice_interface, submitted))

    running = annotationjob_interface.get_with_status("RUNNING")
    updates_running = list(process_running(annotationservice_interface, running))

    annotated = annotationjob_interface.get_with_status(
        ["ANNOTATED", "FAILED (PROCESSING)", "FAILED (DEPOSIT)"]
    )
    updates_annotated = list(
        process_annotated(annotationservice_interface, annotationjob_interface, annotated)
    )

    assert len(updates_submitted) == 1
    assert len(updates_running) == 0
    assert len(updates_annotated) == 0

    id, update = updates_submitted[0]
    assert update["status"] == "RUNNING"
    assert update["task_id"] == "123456789"

    # Update database
    annotationjob_interface.patch(
        id, status=update["status"], message=update["message"], task_id=update["task_id"]
    )

    # Process running #1
    # First call to test annotation service status should return "PENDING" ("RUNNING")
    submitted = annotationjob_interface.get_with_status("SUBMITTED")
    updates_submitted = list(process_submitted(annotationservice_interface, submitted))

    running = annotationjob_interface.get_with_status("RUNNING")
    updates_running = list(process_running(annotationservice_interface, running))

    annotated = annotationjob_interface.get_with_status(
        ["ANNOTATED", "FAILED (PROCESSING)", "FAILED (DEPOSIT)"]
    )
    updates_annotated = list(
        process_annotated(annotationservice_interface, annotationjob_interface, annotated)
    )

    assert len(updates_submitted) == 0
    assert len(updates_running) == 1
    assert len(updates_annotated) == 0

    id, update = updates_running[0]
    assert update["status"] == "RUNNING"
    assert update["task_id"] == "123456789"

    # Process running #2
    # Second call to test annotation service status should return "SUCCESS" ("ANNOTATED")
    submitted = annotationjob_interface.get_with_status("SUBMITTED")
    updates_submitted = list(process_submitted(annotationservice_interface, submitted))

    running = annotationjob_interface.get_with_status("RUNNING")
    updates_running = list(process_running(annotationservice_interface, running))

    annotated = annotationjob_interface.get_with_status(
        ["ANNOTATED", "FAILED (PROCESSING)", "FAILED (DEPOSIT)"]
    )
    updates_annotated = list(
        process_annotated(annotationservice_interface, annotationjob_interface, annotated)
    )

    assert len(updates_submitted) == 0
    assert len(updates_running) == 1
    assert len(updates_annotated) == 0

    id, update = updates_running[0]
    assert update["status"] == "ANNOTATED"
    assert update["task_id"] == "123456789"

    # Update database
    annotationjob_interface.patch(
        id, status=update["status"], message=update["message"], task_id=update["task_id"]
    )

    # Process annotated
    submitted = annotationjob_interface.get_with_status("SUBMITTED")
    updates_submitted = list(process_submitted(annotationservice_interface, submitted))

    running = annotationjob_interface.get_with_status("RUNNING")
    updates_running = list(process_running(annotationservice_interface, running))

    annotated = annotationjob_interface.get_with_status(
        ["ANNOTATED", "FAILED (PROCESSING)", "FAILED (DEPOSIT)"]
    )
    updates_annotated = list(
        process_annotated(annotationservice_interface, annotationjob_interface, annotated)
    )

    assert len(updates_submitted) == 0
    assert len(updates_running) == 0
    assert len(updates_annotated) == 1

    id, update = updates_annotated[0]
    assert re.match("OSError: /tmp/.*? is not valid bcf or vcf .*", update["message"])
