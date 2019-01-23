import json
from api.tests.util import FlaskClientProxy


api = FlaskClientProxy(url_prefix="/api/v1")


uri_part = {"analysis": "analyses", "allele": "alleles"}

ANALYSIS_WORKFLOW = "analysis"


def finalize_template(
    annotations,
    custom_annotations,
    alleleassessments,
    referenceassessments,
    allelereports,
    attachments,
    allele_ids,
    excluded_allele_ids,
    technical_allele_ids,
    notrelevant_allele_ids,
):
    return {
        "annotations": annotations,
        "custom_annotations": custom_annotations,
        "alleleassessments": alleleassessments,
        "referenceassessments": referenceassessments,
        "allelereports": allelereports,
        "attachments": attachments,
        "technical_allele_ids": technical_allele_ids,
        "notrelevant_allele_ids": notrelevant_allele_ids,
        "allele_ids": allele_ids,
        "excluded_allele_ids": excluded_allele_ids,
    }


def round_template(
    annotations=None,
    custom_annotations=None,
    alleleassessments=None,
    allelereports=None,
    allele_ids=None,
    excluded_allele_ids=None,
):
    return {
        "annotations": annotations if annotations else [],
        "custom_annotations": custom_annotations if custom_annotations else [],
        "alleleassessments": alleleassessments if alleleassessments else [],
        "allelereports": allelereports if allelereports else [],
        "allele_ids": allele_ids,
        "excluded_allele_ids": excluded_allele_ids if excluded_allele_ids else {},
    }


def interpretation_template(interpretation):
    return {
        "id": interpretation["id"],
        "user_state": interpretation["user_state"],
        "state": interpretation["state"],
    }


def allele_assessment_template_for_variant_workflow(allele):
    return {
        "allele_id": allele["id"],
        "evaluation": {"comment": "Original comment"},
        "classification": "5",
    }


def allele_assessment_template(workflow_type, workflow_id, allele, extra):
    base = {
        "allele_id": allele["id"],
        "attachments": [],
        "evaluation": {"comment": "Original comment"},
        "classification": "5",
        "analysis_id": None,
        "genepanel_name": None,
        "genepanel_version": None,
    }

    if workflow_type == ANALYSIS_WORKFLOW:
        base["analysis_id"] = workflow_id
        del base["genepanel_name"]
        del base["genepanel_version"]
    else:
        del base["analysis_id"]
        base["genepanel_name"] = extra["genepanel_name"]
        base["genepanel_version"] = extra["genepanel_version"]

    return base


def reference_assessment_template(workflow_type, workflow_id, allele, reference, extra):
    base = {
        "allele_id": allele["id"],
        "reference_id": reference["id"],
        "evaluation": {"comment": "Original comment"},
        "analysis_id": None,
        "genepanel_name": None,
        "genepanel_version": None,
    }

    if workflow_type == ANALYSIS_WORKFLOW:
        base["analysis_id"] = workflow_id
        del base["genepanel_name"]
        del base["genepanel_version"]
    else:
        del base["analysis_id"]
        base["genepanel_name"] = extra["genepanel_name"]
        base["genepanel_version"] = extra["genepanel_version"]

    return base


def allele_report_template(workflow_type, workflow_id, allele, extra):
    base = {
        "allele_id": allele["id"],
        "evaluation": {"comment": "Original comment"},
        "analysis_id": None,
        "genepanel_name": None,
        "genepanel_version": None,
    }

    if workflow_type == ANALYSIS_WORKFLOW:
        base["analysis_id"] = workflow_id
        del base["genepanel_name"]
        del base["genepanel_version"]
    else:
        del base["analysis_id"]
        base["genepanel_name"] = extra["genepanel_name"]
        base["genepanel_version"] = extra["genepanel_version"]

    return base


def get_interpretation_id_of_last(workflow_type, workflow_id):
    response = api.get(
        "/workflows/{}/{}/interpretations/".format(uri_part[workflow_type], workflow_id)
    )
    assert response
    assert response.status_code == 200
    interpretations = response.get_json()
    return interpretations[-1]["id"]


def get_interpretation_id_of_first(workflow_type, workflow_id):
    response = api.get(
        "/workflows/{}/{}/interpretations/".format(uri_part[workflow_type], workflow_id)
    )
    assert response
    assert response.status_code == 200
    interpretations = response.get_json()
    return interpretations[0]["id"]


def get_last_interpretation(workflow_type, id=1):
    return get_interpretation(workflow_type, id, get_interpretation_id_of_last(workflow_type, id))


def get_interpretation(workflow_type, workflow_id, interpretation_id):
    response = api.get(
        "/workflows/{}/{}/interpretations/{}/".format(
            uri_part[workflow_type], workflow_id, interpretation_id
        )
    )
    return response


def get_filtered_alleles(workflow_type, workflow_id, interpretation_id, filterconfig_id=None):
    params = "?filterconfig_id={}".format(filterconfig_id) if filterconfig_id else ""
    assert workflow_type == "analysis"
    response = api.get(
        "/workflows/analyses/{}/interpretations/{}/filteredalleles/{}".format(
            workflow_id, interpretation_id, params
        )
    )
    return response


def get_interpretations(workflow_type, workflow_id):
    response = api.get(
        "/workflows/{}/{}/interpretations/".format(uri_part[workflow_type], workflow_id)
    )
    return response


def save_interpretation_state(workflow_type, interpretation, workflow_id, username):
    return api.patch(
        "/workflows/{}/{}/interpretations/{}/".format(
            uri_part[workflow_type], workflow_id, interpretation["id"]
        ),
        interpretation_template(interpretation),
        username=username,
    )


def start_interpretation(workflow_type, id, username, extra=None):
    post_data = {}
    if extra:
        post_data.update(extra)
    response = api.post(
        "/workflows/{}/{}/actions/start/".format(uri_part[workflow_type], id),
        post_data,
        username=username,
    )
    assert response.status_code == 200
    interpretation = get_last_interpretation(workflow_type, id).get_json()
    assert interpretation["status"] == "Ongoing"
    assert interpretation["user"]["username"] == username
    return interpretation


def create_entities(type, data):
    return api.post("/{}/".format(type), data)


def get_entities_by_query(type, query):
    response = api.get("/{}/?q={}".format(type, json.dumps(query)))
    return response


def get_snapshots(workflow_type, workflow_id):
    response = api.get("/workflows/{}/{}/snapshots/".format(uri_part[workflow_type], workflow_id))
    return response


def get_alleles(workflow_type, workflow_id, interpretation_id, allele_ids):
    response = api.get(
        "/workflows/{}/{}/interpretations/{}/alleles/?allele_ids={}&current=true".format(
            uri_part[workflow_type],
            workflow_id,
            interpretation_id,
            ",".join([str(a) for a in allele_ids]),
        )
    )
    return response


def get_entity_by_id(type, id):  # like /alleleassessments/34/
    response = api.get("/{}/{}/".format(type, id))
    return response


def get_entities_by_allele_id(type, id):
    query_filter = {"allele_id": id}
    response = api.get("/{}/?q={}".format(type, json.dumps(query_filter)))
    return response


def get_allele_assessments_by_allele(allele_id):
    return get_entities_by_allele_id("alleleassessments", allele_id)


def get_allele_reports_by_allele(allele_id):
    return get_entities_by_allele_id("allelereports", allele_id)


def get_reference_assessments_by_allele(allele_id):
    return get_entities_by_allele_id("referenceassessments", allele_id)


def get_users():
    response = api.get("/users/")
    return response


def mark_notready(workflow_type, workflow_id, data, username):
    response = api.post(
        "/workflows/{}/{}/actions/marknotready/".format(uri_part[workflow_type], workflow_id),
        data,
        username=username,
    )
    return response


def mark_interpretation(workflow_type, workflow_id, data, username):
    response = api.post(
        "/workflows/{}/{}/actions/markinterpretation/".format(uri_part[workflow_type], workflow_id),
        data,
        username=username,
    )
    return response


def mark_review(workflow_type, workflow_id, data, username):
    response = api.post(
        "/workflows/{}/{}/actions/markreview/".format(uri_part[workflow_type], workflow_id),
        data,
        username=username,
    )
    return response


def mark_medicalreview(workflow_type, workflow_id, data, username):
    response = api.post(
        "/workflows/{}/{}/actions/markmedicalreview/".format(uri_part[workflow_type], workflow_id),
        data,
        username=username,
    )
    return response


def reopen_analysis(workflow_type, workflow_id, username):
    response = api.post(
        "/workflows/{}/{}/actions/reopen/".format(uri_part[workflow_type], workflow_id),
        {},
        username=username,
    )
    return response


def finalize(
    workflow_type,
    analysis_id,
    annotations,
    custom_annotations,
    alleleassessments,
    referenceassessments,
    allelereports,
    attachments,
    username,
    allele_ids=None,
    excluded_allele_ids=None,
    technical_allele_ids=None,
    notrelevant_allele_ids=None,
):
    response = api.post(
        "/workflows/{}/{}/actions/finalize/".format(uri_part[workflow_type], analysis_id),
        finalize_template(
            annotations,
            custom_annotations,
            alleleassessments,
            referenceassessments,
            allelereports,
            attachments,
            allele_ids,
            excluded_allele_ids if excluded_allele_ids else {},
            technical_allele_ids if technical_allele_ids else [],
            notrelevant_allele_ids if notrelevant_allele_ids else [],
        ),
        username=username,
    )
    return response
