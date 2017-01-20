import json
from api.tests.util import FlaskClientProxy


api = FlaskClientProxy(url_prefix='/api/v1')


def finalize_template(annotations, custom_annotations, alleleassessments, referenceassessments, allelereports):
    return {
       'annotations': annotations,
       'custom_annotations': custom_annotations,
       'alleleassessments': alleleassessments,
       'referenceassessments': referenceassessments,
       'allelereports': allelereports
}


def review_template(annotations = None, custom_annotations = None, alleleassessments = None, allelereports = None):
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
        'user_id': interpretation['user_id']
    }


def allele_assessment_template(analysis_id, allele, user):
    return {
        'user_id': user['id'],
        'allele_id': allele['id'],
        'evaluation': {'comment': 'Original comment'},
        'classification': 5,
        'analysis_id': analysis_id
    }


def reference_assessment_template(analysis_id, allele, reference, user):
    return {
        'user_id': user['id'],
        'allele_id': allele['id'],
        'reference_id': reference['id'],
        'evaluation': {'comment': 'Original comment'},
        'analysis_id': analysis_id
    }


def allele_report_template(analysis_id, allele, user):
    return {
        'user_id': user['id'],
        'allele_id': allele['id'],
        'evaluation': {'comment': 'Original comment'},
        'analysis_id': analysis_id
    }


def get_last_interpretation_id(analysis_id=1):
    r = api.get('/analyses/{}/'.format(analysis_id)).json
    return r['interpretations'][-1]['id']


def get_interpretation_id_of_first(analysis_id):
    r = api.get('/analyses/{}/'.format(analysis_id)).json
    return r['interpretations'][0]['id']


def get_last_interpretation(analysis_id=1):
    return get_interpretation(analysis_id, get_last_interpretation_id(analysis_id=analysis_id))


def get_interpretation(analysis_id, interpretation_id):
    return api.get('/workflows/analyses/{}/interpretations/{}/'
        .format(analysis_id, interpretation_id)).json


def save_interpretation_state(interpretation, analysis_id):
    api.patch(
    '/workflows/analyses/{}/interpretations/{}/'
        .format(analysis_id, interpretation['id']),
        interpretation_template(interpretation)
    )


def start_analysis(analysis_id, user):
    response = api.post(
        '/workflows/analyses/{}/actions/start/'.format(analysis_id),
        {'user_id': user['id']}
    )
    assert response.status_code == 200
    interpretation = get_last_interpretation(analysis_id)
    assert interpretation['status'] == 'Ongoing'
    return interpretation


def create_entities(type, data):
    return api.post('/{}/'.format(type), data)


def get_entities_by_query(type, query):
    response = api.get('/{}/?q={}'.format(type, json.dumps(query)))
    assert response.status_code == 200
    return response.json


def get_snapshots(analysis_id):
    response = api.get('/workflows/analyses/{}/snapshots/'.format(analysis_id))
    assert response.status_code == 200
    snapshots = response.json
    assert snapshots
    return snapshots


def get_alleles(ids):
    response = api.get('/alleles/?q={}&gp_name={}&gp_version={}'.format(json.dumps({'id': ids}), 'HBOCUTV', 'v01'))
    assert response.status_code == 200
    return response.json


def get_entity_by_id(type, id):  # like /alleleassessments/34/
    response = api.get('/{}/{}/'.format(type, id))
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


def get_analysis(id):
    return get_entity_by_id('analyses', id)


def mark_review(analysis_id, data):
    response = api.post(
        '/workflows/analyses/{}/actions/markreview/'.format(analysis_id),
        data
    )
    assert response.status_code == 200


def reopen_analysis(user, analysis_id):
    response = api.post(
        '/workflows/analyses/{}/actions/reopen/'.format(analysis_id),
        {'user_id': user['id']}
    )
    assert response.status_code == 200


def finalize(analysis_id,
             annotations,
             custom_annotations,
             alleleassessments,
             referenceassessments,
             allelereports):
    response = api.post(
        '/workflows/analyses/{}/actions/finalize/'.format(analysis_id),
        finalize_template(annotations, custom_annotations, alleleassessments, referenceassessments, allelereports)
    )
    assert response.status_code == 200
    return response.json