"""Testing is done by using a dummy annotation server.
This server is specified in /ella/ops/test/testannotationserver.py
and started in conftest.py"""

import json

from api.polling import ANNOTATION_JOBS_PATH
from api.polling import process_annotated, process_submitted, process_running, db_job_update

def test_annotationserver_running(client):
    response = client.get('/api/v1/annotationservice/running/')
    assert response.status_code == 200
    assert json.loads(response.get_data())["running"]


def test_polling(client):
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


    client = client.app.test_client()
    # Process submitted
    submitted_jobs = list(process_submitted(client))
    running_jobs = list(process_running(client))
    annotated_jobs = list(process_annotated(client))
    assert len(submitted_jobs) == 1
    assert len(running_jobs) == 0
    assert len(annotated_jobs) == 0

    job = submitted_jobs[0]
    assert job["status"] == "RUNNING"
    assert job["task_id"] == "123456789"

    # Update database
    response = db_job_update(client, job)
    assert response.status_code == 200

    # Process running #1
    submitted_jobs = list(process_submitted(client))
    running_jobs = list(process_running(client))
    annotated_jobs = list(process_annotated(client))
    assert len(submitted_jobs) == 0
    assert len(running_jobs) == 1
    assert len(annotated_jobs) == 0

    job = running_jobs[0]
    assert job["status"] == "RUNNING"
    assert job["task_id"] == "123456789"

    # Process running #2
    submitted_jobs = list(process_submitted(client))
    running_jobs = list(process_running(client))
    annotated_jobs = list(process_annotated(client))
    assert len(submitted_jobs) == 0
    assert len(running_jobs) == 1
    assert len(annotated_jobs) == 0

    job = running_jobs[0]
    assert job["status"] == "ANNOTATED"
    assert job["task_id"] == "123456789"

    # Update database
    response = db_job_update(client, job)
    assert response.status_code == 200

    # Process annotated
    submitted_jobs = list(process_submitted(client))
    running_jobs = list(process_running(client))

    # Expected failure
    try:
        annotated_jobs = list(process_annotated(client))
        error_message = None
    except RuntimeError as e:
        error_message = e.message

    assert error_message == "Couldn't import samples to database."
    assert len(submitted_jobs) == 0
    assert len(running_jobs) == 0
