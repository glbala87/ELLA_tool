from api.tests.workflow_helper import WorkflowHelper
from api.tests import interpretation_helper as ih

ALLELE_ID = 1
ANALYSIS_ID = 1
FILTERCONFIG_ID = 1


def check_log(
    log,
    message=None,
    review_comment=None,
    priority=None,
    warning_cleared=None,
    alleleassessment=False,
):
    # Only one of these can be given at a time
    assert (
        len(
            [k for k in [message, review_comment, priority, warning_cleared, alleleassessment] if k]
        )
        == 1
    )

    assert log["message"] == message
    assert log["review_comment"] == review_comment
    assert log["priority"] == priority
    assert log["warning_cleared"] == warning_cleared
    assert bool(log["alleleassessment"]) == alleleassessment


def check_latest_log(
    client,
    workflow_type,
    message=None,
    review_comment=None,
    priority=None,
    warning_cleared=None,
    editable=False,
    alleleassessment=False,
):
    url_type = "alleles" if workflow_type == "allele" else "analyses"
    r = client.get("/api/v1/workflows/{}/{}/logs/".format(url_type, ALLELE_ID))
    logs = r.get_json()["logs"]
    print(logs)
    check_log(
        logs[-1],
        message=message,
        review_comment=review_comment,
        priority=priority,
        warning_cleared=warning_cleared,
        alleleassessment=alleleassessment,
    )
    assert logs[-1]["editable"] is editable
    return logs[-1]


def test_allele_workflow(client, test_database):

    test_database.refresh()  # Reset db

    # Insert message
    message = "Message 1"
    data = {"message": message}
    resp = client.post("/api/v1/workflows/alleles/{}/logs/".format(ALLELE_ID), data=data)
    assert resp.status_code == 200

    log = check_latest_log(client, "allele", message=message, editable=True)

    # Edit message
    log_id = log["id"]
    message = "Message 1, edited"
    data = {"message": message}
    resp = client.patch(
        "/api/v1/workflows/alleles/{}/logs/{}/".format(ALLELE_ID, log_id), data=data
    )

    check_latest_log(client, "allele", message=message, editable=True)

    # Make sure it's not editable after one round
    allele_wh = WorkflowHelper("allele", ALLELE_ID, "HBOCUTV", "v01")
    interpretation = allele_wh.start_interpretation("testuser1")
    allele_wh.perform_round(interpretation, "Some comment", new_workflow_status="Interpretation")

    check_latest_log(client, "allele", message=message, editable=False)

    # Insert another message
    message = "Message 2"
    data = {"message": message}
    resp = client.post("/api/v1/workflows/alleles/{}/logs/".format(ALLELE_ID), data=data)
    assert resp.status_code == 200

    log = check_latest_log(client, "allele", message=message, editable=True)

    # Insert review comment
    review_comment = "Review comment 1"
    data = {"review_comment": review_comment}
    resp = client.post("/api/v1/workflows/alleles/{}/logs/".format(ALLELE_ID), data=data)
    assert resp.status_code == 200

    check_latest_log(client, "allele", review_comment=review_comment, editable=False)

    # Insert priority
    data = {"priority": 2}
    resp = client.post("/api/v1/workflows/alleles/{}/logs/".format(ALLELE_ID), data=data)
    assert resp.status_code == 200

    check_latest_log(client, "allele", priority=2, editable=False)

    # Clear warning (not allowed for alleles)
    data = {"warning_cleared": True}

    resp = client.post("/api/v1/workflows/alleles/{}/logs/".format(ALLELE_ID), data=data)
    assert resp.status_code == 500

    # Finalize to create alleleassessment
    interpretation = allele_wh.start_interpretation("testuser1")
    allele_wh.perform_finalize_round(interpretation, "Finalize comment")
    check_latest_log(client, "allele", alleleassessment=True, editable=False)


def test_analyses_workflow(client, test_database):

    test_database.refresh()  # Reset db

    # Insert message
    message = "Message 1"
    data = {"message": message}
    resp = client.post("/api/v1/workflows/analyses/{}/logs/".format(ANALYSIS_ID), data=data)
    assert resp.status_code == 200

    log = check_latest_log(client, "analysis", message=message, editable=True)

    # Edit message
    log_id = log["id"]
    message = "Message 1, edited"
    data = {"message": message}
    resp = client.patch(
        "/api/v1/workflows/analyses/{}/logs/{}/".format(ANALYSIS_ID, log_id), data=data
    )

    check_latest_log(client, "analysis", message=message, editable=True)

    # Make sure it's not editable after one round
    analysis_wh = WorkflowHelper(
        "analysis", ANALYSIS_ID, "HBOC", "v01", filterconfig_id=FILTERCONFIG_ID
    )
    interpretation = analysis_wh.start_interpretation("testuser1")
    analysis_wh.perform_round(interpretation, "Some comment", new_workflow_status="Interpretation")

    check_latest_log(client, "analysis", message=message, editable=False)

    # Insert another message
    message = "Message 2"
    data = {"message": message}
    resp = client.post("/api/v1/workflows/analyses/{}/logs/".format(ANALYSIS_ID), data=data)
    assert resp.status_code == 200

    log = check_latest_log(client, "analysis", message=message, editable=True)

    # Insert review comment
    review_comment = "Review comment 1"
    data = {"review_comment": review_comment}
    resp = client.post("/api/v1/workflows/analyses/{}/logs/".format(ANALYSIS_ID), data=data)
    assert resp.status_code == 200

    check_latest_log(client, "analysis", review_comment=review_comment, editable=False)

    # Insert priority
    data = {"priority": 2}
    resp = client.post("/api/v1/workflows/analyses/{}/logs/".format(ANALYSIS_ID), data=data)
    assert resp.status_code == 200

    check_latest_log(client, "analysis", priority=2, editable=False)

    # Clear warning
    data = {"warning_cleared": True}
    resp = client.post("/api/v1/workflows/analyses/{}/logs/".format(ANALYSIS_ID), data=data)
    assert resp.status_code == 200

    check_latest_log(client, "analysis", warning_cleared=True, editable=False)

    # Finalize to create alleleassessment
    # perform_finalize_round creates one assessment per allele
    interpretation = analysis_wh.start_interpretation("testuser1")
    filtered_allele_ids = ih.get_filtered_alleles(
        "analysis", ANALYSIS_ID, interpretation["id"], filterconfig_id=FILTERCONFIG_ID
    ).get_json()["allele_ids"]
    analysis_wh.perform_finalize_round(interpretation, "Finalize comment")
    r = client.get("/api/v1/workflows/analyses/{}/logs/".format(ALLELE_ID))
    logs = r.get_json()["logs"]
    filtered_allele_ids_cnt = len(filtered_allele_ids)
    created_aa_allele_ids = set(
        l["alleleassessment"]["allele_id"] for l in logs[-filtered_allele_ids_cnt:]
    )
    assert set(created_aa_allele_ids) == set(filtered_allele_ids)
