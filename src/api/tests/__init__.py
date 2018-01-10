import json
from api.tests.util import FlaskClientProxy


api = FlaskClientProxy(url_prefix='/api/v1')


uri_part = {"analysis": "analyses",
            "variant": "alleles"
            }

ANALYSIS_WORKFLOW = "analysis"
VARIANT_WORKFLOW = "variant"


def finalize_template(annotations, custom_annotations, alleleassessments, referenceassessments, allelereports, attachments):
    return {
       'annotations': annotations,
       'custom_annotations': custom_annotations,
       'alleleassessments': alleleassessments,
       'referenceassessments': referenceassessments,
       'allelereports': allelereports,
       'attachments': attachments,
}


def review_template(annotations=None, custom_annotations=None, alleleassessments=None, allelereports=None):
    return {
       'annotations': annotations if annotations else [],
       'custom_annotations': custom_annotations if custom_annotations else [],
       'alleleassessments': alleleassessments if alleleassessments else [],
       'allelereports': allelereports if allelereports else []
}


def interpretation_template(interpretation):
    return {
        'id': interpretation['id'],
        'user_state': interpretation['user_state'],
        'state': interpretation['state'],
    }


def allele_assessment_template_for_variant_workflow(allele):
    return {
        'allele_id': allele['id'],
        'evaluation': {'comment': 'Original comment'},
        'classification': '5'
    }


def allele_assessment_template(workflow_type, workflow_id, allele, extra):
    base = {
            'allele_id': allele['id'],
            'attachments': [],
            'evaluation': {'comment': 'Original comment'},
            'classification': '5',
            'analysis_id': None,
            'genepanel_name': None,
            'genepanel_version': None
            }

    if workflow_type == ANALYSIS_WORKFLOW:
        base['analysis_id'] = workflow_id
        del base['genepanel_name']
        del base['genepanel_version']
    else:
        del base['analysis_id']
        base['genepanel_name'] = extra['genepanel_name']
        base['genepanel_version'] = extra['genepanel_version']

    return base


def reference_assessment_template(workflow_type, workflow_id, allele, reference, extra):
    base = {
        'allele_id': allele['id'],
        'reference_id': reference['id'],
        'evaluation': {'comment': 'Original comment'},
        'analysis_id': None,
        'genepanel_name': None,
        'genepanel_version': None
    }

    if workflow_type == ANALYSIS_WORKFLOW:
        base['analysis_id'] = workflow_id
        del base['genepanel_name']
        del base['genepanel_version']
    else:
        del base['analysis_id']
        base['genepanel_name'] = extra['genepanel_name']
        base['genepanel_version'] = extra['genepanel_version']

    return base


def allele_report_template(workflow_type, workflow_id, allele, extra):
    base = {
        'allele_id': allele['id'],
        'evaluation': {'comment': 'Original comment'},
        'analysis_id': None,
        'genepanel_name': None,
        'genepanel_version': None
    }

    if workflow_type == ANALYSIS_WORKFLOW:
        base['analysis_id'] = workflow_id
        del base['genepanel_name']
        del base['genepanel_version']
    else:
        del base['analysis_id']
        base['genepanel_name'] = extra['genepanel_name']
        base['genepanel_version'] = extra['genepanel_version']

    return base


def get_interpretation_id_of_last(workflow_type, workflow_id):
    response = api.get('/workflows/{}/{}/interpretations/'.format(uri_part[workflow_type], workflow_id))
    assert response
    assert response.status_code == 200
    interpretations = response.json
    return interpretations[-1]['id']


def get_interpretation_id_of_first(workflow_type, workflow_id):
    response = api.get('/workflows/{}/{}/interpretations/'.format(uri_part[workflow_type], workflow_id))
    assert response
    assert response.status_code == 200
    interpretations = response.json
    return interpretations[0]['id']


def get_last_interpretation(workflow_type, id=1):
    return get_interpretation(workflow_type, id, get_interpretation_id_of_last(workflow_type, id))


def get_interpretation(workflow_type, workflow_id, interpretation_id):
    response = api.get(
        '/workflows/{}/{}/interpretations/{}/'.format(uri_part[workflow_type], workflow_id, interpretation_id))
    assert response
    assert response.status_code == 200
    interpretation = response.json
    return interpretation


def get_interpretations(workflow_type, workflow_id):
    response = api.get(
        '/workflows/{}/{}/interpretations/'.format(uri_part[workflow_type], workflow_id)
    )
    assert response
    assert response.status_code == 200
    interpretations = response.json
    return interpretations


def save_interpretation_state(workflow_type, interpretation, workflow_id, user):
    api.patch(
        '/workflows/{}/{}/interpretations/{}/'
        .format(uri_part[workflow_type], workflow_id, interpretation['id']),
        interpretation_template(interpretation),
        username=user['username']
    )


def start_interpretation(workflow_type, id, user, extra=None):
    post_data = {}
    if extra:
        for k, v in extra.iteritems():
            post_data[k] = v
    response = api.post(
        '/workflows/{}/{}/actions/start/'.format(uri_part[workflow_type], id),
        post_data,
        username=user['username']
    )
    assert response.status_code == 200
    interpretation = get_last_interpretation(workflow_type, id)
    assert interpretation['status'] == 'Ongoing'
    assert interpretation['user']['username'] == user['username']
    return interpretation


def create_entities(type, data):
    return api.post('/{}/'.format(type), data)


def get_entities_by_query(type, query):
    response = api.get('/{}/?q={}'.format(type, json.dumps(query)))
    assert response.status_code == 200
    return response.json


def get_snapshots(workflow_type, workflow_id):
    response = api.get('/workflows/{}/{}/snapshots/'.format(uri_part[workflow_type], workflow_id))
    assert response
    assert response.status_code == 200
    snapshots = response.json
    return snapshots


def get_alleles(ids):
    response = api.get('/alleles/?q={}&gp_name={}&gp_version={}'.format(json.dumps({'id': ids}), 'HBOCUTV', 'v01'))
    assert response.status_code == 200
    return response.json


def get_entity_by_id(type, id):  # like /alleleassessments/34/
    response = api.get('/{}/{}/'.format(type, id))
    assert response
    assert response.status_code == 200
    return response.json


def get_entities_by_analysis_id(type, id):
    analysis_query_filter = {'analysis_id': id}
    response = api.get('/{}/?q={}'.format(type, json.dumps(analysis_query_filter)))
    assert response.status_code == 200
    return response.json


def get_allele_assessments_by_analysis(analysis_id):
    return get_entities_by_analysis_id('alleleassessments', analysis_id)


def get_allele_reports_by_analysis(analysis_id):
    return get_entities_by_analysis_id('allelereports', analysis_id)


def get_reference_assessments_by_analysis(analysis_id):
    return get_entities_by_analysis_id('referenceassessments', analysis_id)


def get_users():
    response = api.get('/users/')
    assert response.status_code == 200
    return response.json


def get_analysis_workflow(id):
    return get_entity_by_id('analyses', id)


def get_variant_workflow(id):
    return get_entity_by_id('variants', id)


def mark_review(workflow_type, workflow_id, data, user):
    response = api.post(
        '/workflows/{}/{}/actions/markreview/'.format(uri_part[workflow_type], workflow_id),
        data,
        username=user['username']
    )
    assert response.status_code == 200


def reopen_analysis(workflow_type, workflow_id, user):
    response = api.post(
        '/workflows/{}/{}/actions/reopen/'.format(uri_part[workflow_type], workflow_id),
        {},
        username=user['username']
    )
    assert response.status_code == 200


def finalize(workflow_type, analysis_id, annotations, custom_annotations, alleleassessments, referenceassessments,
             allelereports, attachments, user):
    response = api.post(
        '/workflows/{}/{}/actions/finalize/'.format(uri_part[workflow_type], analysis_id),
        finalize_template(annotations, custom_annotations, alleleassessments, referenceassessments, allelereports, attachments),
        username=user['username']
    )
    assert response.status_code == 200
    return response.json
