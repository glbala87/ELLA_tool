"""Testing is done by using a dummy annotation server.
This server is specified in /ella/ops/test/testannotationserver.py
and started in conftest.py"""

import json

#from api.polling import ANNOTATION_JOBS_PATH
from api.polling import AnnotationJobsInterface, AnnotationServiceInterface, \
    ANNOTATION_SERVICE_URL
from api.polling import process_annotated, process_submitted, process_running
ANNOTATION_JOBS_PATH = "/api/v1/annotationjobs/"

def test_annotationserver_running(client):
    response = client.get('/api/v1/annotationservice/running/')
    assert response.status_code == 200
    assert json.loads(response.get_data())["running"]


def test_polling(session, client, test_database):
    test_database.refresh()
    # Submit to database
    data = dict(mode="Analysis",
                user_id=1,
                vcf="Dummy vcf data for testing",
                properties=dict(
                    analysis_name="abc",
                    create_or_append="Create",
                    genepanel="HBOC_v01",
                ))

    response = client.post(ANNOTATION_JOBS_PATH, data=data)
    assert response.status_code == 200

    annotationjob_interface = AnnotationJobsInterface(session)
    annotationservice_interface = AnnotationServiceInterface(ANNOTATION_SERVICE_URL)

    # Process submitted
    submitted = annotationjob_interface.get_with_status("SUBMITTED")
    updates_submitted = list(process_submitted(annotationservice_interface, submitted))

    running = annotationjob_interface.get_with_status("RUNNING")
    updates_running = list(process_running(annotationservice_interface, running))

    annotated = annotationjob_interface.get_with_status(["ANNOTATED", "FAILED (PROCESSING)", "FAILED (DEPOSIT)"])
    updates_annotated = list(process_annotated(annotationservice_interface, annotationjob_interface, annotated))

    assert len(updates_submitted) == 1
    assert len(updates_running) == 0
    assert len(updates_annotated) == 0


    id, update = updates_submitted[0]
    assert update["status"] == "RUNNING"
    assert update["task_id"] == "123456789"

    # Update database
    annotationjob_interface.patch(id, status=update["status"], message=update["message"], task_id=update["task_id"])

    # Process running #1
    # First call to test annotation service status should return "PENDING" ("RUNNING")
    submitted=annotationjob_interface.get_with_status("SUBMITTED")
    updates_submitted=list(process_submitted(annotationservice_interface, submitted))

    running=annotationjob_interface.get_with_status("RUNNING")
    updates_running=list(process_running(annotationservice_interface, running))

    annotated=annotationjob_interface.get_with_status(["ANNOTATED", "FAILED (PROCESSING)", "FAILED (DEPOSIT)"])
    updates_annotated=list(process_annotated(annotationservice_interface, annotationjob_interface, annotated))

    assert len(updates_submitted) == 0
    assert len(updates_running) == 1
    assert len(updates_annotated) == 0

    id, update = updates_running[0]
    assert update["status"] == "RUNNING"
    assert update["task_id"] == "123456789"

    # Process running #2
    # Second call to test annotation service status should return "SUCCESS" ("ANNOTATED")
    submitted=annotationjob_interface.get_with_status("SUBMITTED")
    updates_submitted=list(process_submitted(annotationservice_interface, submitted))

    running=annotationjob_interface.get_with_status("RUNNING")
    updates_running=list(process_running(annotationservice_interface, running))

    annotated=annotationjob_interface.get_with_status(["ANNOTATED", "FAILED (PROCESSING)", "FAILED (DEPOSIT)"])
    updates_annotated=list(process_annotated(annotationservice_interface, annotationjob_interface, annotated))

    assert len(updates_submitted) == 0
    assert len(updates_running) == 1
    assert len(updates_annotated) == 0

    id, update = updates_running[0]
    assert update["status"] == "ANNOTATED"
    assert update["task_id"] == "123456789"

    # Update database
    annotationjob_interface.patch(id, status=update["status"], message=update["message"], task_id=update["task_id"])

    # Process annotated
    submitted=annotationjob_interface.get_with_status("SUBMITTED")
    updates_submitted=list(process_submitted(annotationservice_interface, submitted))

    running=annotationjob_interface.get_with_status("RUNNING")
    updates_running=list(process_running(annotationservice_interface, running))

    annotated=annotationjob_interface.get_with_status(["ANNOTATED", "FAILED (PROCESSING)", "FAILED (DEPOSIT)"])
    updates_annotated=list(process_annotated(annotationservice_interface, annotationjob_interface, annotated))

    assert len(updates_submitted) == 0
    assert len(updates_running) == 0
    assert len(updates_annotated) == 1

    id, update = updates_annotated[0]
    assert update["message"] == "Couldn't import samples to database."
