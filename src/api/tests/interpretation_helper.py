from typing import Sequence, Optional
import json
from api.tests.util import FlaskClientProxy


api = FlaskClientProxy(url_prefix="/api/v1")


uri_part = {"analysis": "analyses", "allele": "alleles"}

ANALYSIS_WORKFLOW = "analysis"


def finalize_allele_template(
    allele_id: int,
    annotation_id: int,
    custom_annotation_id: Optional[int],
    alleleassessment: dict,
    allelereport: dict,
    referenceassessments: Sequence[dict],
):
    data = {
        "allele_id": allele_id,
        "annotation_id": annotation_id,
        "custom_annotation_id": custom_annotation_id,
        "alleleassessment": alleleassessment,
        "allelereport": allelereport,
        "referenceassessments": referenceassessments,
    }
    return data


def finalize_wf_allele_template(
    annotation_ids: Sequence[int],
    custom_annotation_ids: Sequence[int],
    alleleassessment_ids: Sequence[int],
    allelereport_ids: Sequence[int],
    allele_ids: Sequence[int],
):
    return {
        "annotation_ids": annotation_ids,
        "custom_annotation_ids": custom_annotation_ids,
        "alleleassessment_ids": alleleassessment_ids,
        "allelereport_ids": allelereport_ids,
        "allele_ids": allele_ids,
    }


def finalize_wf_analysis_template(
    annotation_ids: Sequence[int],
    custom_annotation_ids: Sequence[int],
    alleleassessment_ids: Sequence[int],
    allelereport_ids: Sequence[int],
    allele_ids: Sequence[int],
    excluded_allele_ids: dict,
    technical_allele_ids: Sequence[int],
    notrelevant_allele_ids: Sequence[int],
):
    return {
        "annotation_ids": annotation_ids,
        "custom_annotation_ids": custom_annotation_ids,
        "alleleassessment_ids": alleleassessment_ids,
        "allelereport_ids": allelereport_ids,
        "allele_ids": allele_ids,
        "excluded_allele_ids": excluded_allele_ids,
        "technical_allele_ids": technical_allele_ids,
        "notrelevant_allele_ids": notrelevant_allele_ids,
    }


def round_template(
    annotation_ids=None,
    custom_annotation_ids=None,
    alleleassessment_ids=None,
    allelereport_ids=None,
    allele_ids=None,
    excluded_allele_ids=None,
):
    return {
        "annotation_ids": annotation_ids if annotation_ids else [],
        "custom_annotation_ids": custom_annotation_ids if custom_annotation_ids else [],
        "alleleassessment_ids": alleleassessment_ids if alleleassessment_ids else [],
        "allelereport_ids": allelereport_ids if allelereport_ids else [],
        "allele_ids": allele_ids,
        "excluded_allele_ids": excluded_allele_ids if excluded_allele_ids else {},
    }


def interpretation_template(interpretation):
    return {
        "id": interpretation["id"],
        "user_state": interpretation["user_state"],
        "state": interpretation["state"],
    }


def allele_assessment_template(allele_id, genepanel_name, genepanel_version):
    return {
        "reuse": False,
        "allele_id": allele_id,
        "attachment_ids": [],
        "evaluation": {
            "acmg": {"included": [], "suggested": []},
            "external": {"comment": "Original comment"},
            "frequency": {"comment": "Original comment"},
            "reference": {"comment": "Original comment"},
            "prediction": {"comment": "Original comment"},
            "classification": {"comment": "Original comment"},
        },
        "classification": "5",
        "genepanel_name": genepanel_name,
        "genepanel_version": genepanel_version,
    }


def reference_assessment_template(allele_id, reference_id, genepanel_name, genepanel_version):
    return {
        "allele_id": allele_id,
        "reference_id": reference_id,
        "evaluation": {"comment": "Original comment"},
        "genepanel_name": genepanel_name,
        "genepanel_version": genepanel_version,
    }


def allele_report_template(allele_id):
    return {"reuse": False, "allele_id": allele_id, "evaluation": {"comment": "Original comment"}}


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


def finalize_allele(
    workflow_type,
    workflow_id,
    allele_id,
    annotation_id,
    custom_annotation_id,
    alleleassessment,
    allelereport,
    referenceassessments,
    username,
):
    response = api.post(
        "/workflows/{}/{}/actions/finalizeallele/".format(uri_part[workflow_type], workflow_id),
        finalize_allele_template(
            allele_id,
            annotation_id,
            custom_annotation_id,
            alleleassessment,
            allelereport,
            referenceassessments,
        ),
        username=username,
    )
    return response


def finalize(
    workflow_type,
    workflow_id,
    allele_ids,
    annotation_ids,
    custom_annotation_ids,
    alleleassessment_ids,
    allelereport_ids,
    username,
    excluded_allele_ids=None,
    technical_allele_ids=None,
    notrelevant_allele_ids=None,
):
    if workflow_type == "allele":
        payload = finalize_wf_allele_template(
            annotation_ids,
            custom_annotation_ids,
            alleleassessment_ids,
            allelereport_ids,
            allele_ids,
        )
    else:
        payload = finalize_wf_analysis_template(
            annotation_ids,
            custom_annotation_ids,
            alleleassessment_ids,
            allelereport_ids,
            allele_ids,
            excluded_allele_ids if excluded_allele_ids else {},
            technical_allele_ids if technical_allele_ids else [],
            notrelevant_allele_ids if notrelevant_allele_ids else [],
        )
    response = api.post(
        "/workflows/{}/{}/actions/finalize/".format(uri_part[workflow_type], workflow_id),
        payload,
        username=username,
    )
    return response
