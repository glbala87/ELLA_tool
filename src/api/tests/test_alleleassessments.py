import json
import copy
import pytest

from util import FlaskClientProxy
from api import ApiError


@pytest.fixture
def assessment_template():
    return {
        "allele_id": 1,
        "annotation_id": 1,
        "analysis_id": 1,
        "user_id": 1,
        "classification": "1",
        "evaluation": {
            "comment": "Some comment",
        },
        "referenceassessments": []  # populated as part of test see referenceassessment_template
    }


def referenceassessment_template(allele_id):
    return {
        "allele_id": allele_id,
        "analysis_id": 1,
        "user_id": 1,
        "reference_id": 9,  # must exist in database
        "evaluation": {
            "comment": "Some comment"
        },
    }


@pytest.fixture
def client():
    return FlaskClientProxy()


class TestAlleleAssessment(object):

    def _get_interpretation_id_of_first(self, client):
        r = client.get('/api/v1/analyses/1/').json
        return r['interpretations'][0]['id']

    def _get_interpretation(self, client, id):
        return client.get('/api/v1/interpretations/{}/'.format(id)).json

    @pytest.mark.aa(order=0)
    def test_create_new(self, test_database, assessment_template, client):
        test_database.refresh()  # Reset db

        # Create an assessment for alleles in the interpretation
        interpretation = self._get_interpretation(client, self._get_interpretation_id_of_first(client))
        for idx, allele_id in enumerate(interpretation['allele_ids']):

            # Prepare
            assessment_data = copy.deepcopy(assessment_template)
            assessment_data['allele_id'] = allele_id
            assessment_data['referenceassessments'] = [referenceassessment_template(allele_id)]

            annotations = [{"allele_id": assessment_data['allele_id'], "annotation_id": assessment_data['annotation_id']}]

            # POST data
            r = client.post('/api/v1/alleleassessments/', {"annotations": annotations,
                                                           "allele_assessments": [assessment_data]})

            # Check response
            assert r.status_code == 200
            assessment_data = r.json[0]
            assert len(assessment_data['referenceassessments']) == 1
            assert 'id' in assessment_data['referenceassessments'][0]
            assert assessment_data['referenceassessments'][0]['allele_id'] == allele_id
            assert assessment_data['allele_id'] == allele_id
            assert assessment_data['id'] == idx + 1

    @pytest.mark.aa(order=1)
    def test_update_assessment(self, client):
        """
        Simulate updating the AlleleAssessment created in create_new().
        It should result in a new AlleleAssessment being created,
        while the existing should be superceded.
        """

        interpretation = self._get_interpretation(client, self._get_interpretation_id_of_first(client))

        q = {'allele_id': interpretation['allele_ids'], 'date_superceeded': None}
        previous_assessments = client.get('/api/v1/alleleassessments/?q={}'.format(json.dumps(q))).json

        previous_ids = []
        for assessment_data in previous_assessments:
            # Build assessment data suitable for saving
            prev_id = assessment_data['id']
            previous_ids.append(prev_id)  # bookkeeping
            # Delete the id, to make the backend create a new assessment
            del assessment_data['id']
            del assessment_data['previous_assessment_id']  # remove as a null value creates an schema exception
            assessment_data['presented_alleleassessment_id'] = prev_id  # Api requirement dictated by finalization
            assessment_data['reuse'] = False
            assessment_data['evaluation']['comment'] = "A new assessment superceeding an old one"

            # Update referenceassessment
            prev_ra_id = assessment_data['referenceassessments'][0]['id']
            del assessment_data['referenceassessments'][0]['id']
            assessment_data['referenceassessments'][0]['evaluation'] = {'comment': 'Some new reference comment'}

            # POST (a single) assessment
            annotations = [{"allele_id": assessment_data['allele_id'], "annotation_id": assessment_data['annotation_id']}]
            r = client.post('/api/v1/alleleassessments/', {"annotations": annotations,
                                                           "allele_assessments": [assessment_data]})

            # Check response
            assert r.status_code == 200
            new_assessment = r.json[0]  # we posted only one, so expect only one in return
            assert new_assessment['id'] != prev_id
            assert new_assessment['evaluation']['comment'] == 'A new assessment superceeding an old one'

            # Check that a new referenceassessment was created
            assert new_assessment['referenceassessments'][0]['id'] != prev_ra_id
            assert new_assessment['referenceassessments'][0]['evaluation']['comment'] == 'Some new reference comment'

        # Reload the previous alleleassessments and make sure
        # they're marked as superceded
        q = {'id': previous_ids}
        previous_assessments = client.get('/api/v1/alleleassessments/?q={}'.format(json.dumps(q))).json

        assert all([p['date_superceeded'] is not None for p in previous_assessments])

    @pytest.mark.aa(order=2)
    def test_fail_cases(self, client, assessment_template):
        """
        Test cases where it should fail to create assessments.
        """

        assessment_data = copy.deepcopy(assessment_template)
        annotations = [{"annotation_id": 1, "allele_id": assessment_data['allele_id']}]

        # Test without allele_id
        del assessment_data['allele_id']

        # We don't run actual HTTP requests, everything is in python
        # so we can catch the exceptions directly
        with pytest.raises(Exception):  # the error is not caught at the API boundary as enforcing required fields for dict of dict isn't implemented
            client.post('/api/v1/alleleassessments/', {"annotations": annotations,
                                                       "allele_assessments": [assessment_data]})

        # Test without analysis_id
        assessment_data = copy.deepcopy(assessment_template)
        del assessment_data['analysis_id']

        with pytest.raises(ApiError):
            client.post('/api/v1/alleleassessments/', {"annotations": annotations,
                                                       "allele_assessments": [assessment_data]})
