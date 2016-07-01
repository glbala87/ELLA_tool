import json
import copy
import pytest

from util import FlaskClientProxy
from api import ApiError


@pytest.fixture
def testdata():
    return {
        "allele_id": 1,
        "classification": "1",
        "evaluation": {
            "comment": "Some comment",
        },
        "user_id": 1,
        "analysis_id": 1,
        "referenceassessments": []
    }


@pytest.fixture
def client():
    return FlaskClientProxy()


class TestAlleleAssessment(object):

    def _get_interpretation_id(self, client):
        r = client.get('/api/v1/analyses/1/').json
        return r['interpretations'][0]['id']

    def _get_interpretation(self, client):
        return client.get('/api/v1/interpretations/{}/'.format(self._get_interpretation_id(client))).json

    @pytest.mark.aa(order=0)
    def test_create_new(self, test_database, testdata, client):
        test_database.refresh()  # Reset db

        # Retrieve alleles for interpretation for which
        # to create new AlleleAssessments
        interpretation = self._get_interpretation(client)

        # Create all AlleleAssessments objects
        for idx, allele_id in enumerate(interpretation['allele_ids']):

            # Prepare
            aa = copy.deepcopy(testdata)
            aa['allele_id'] = allele_id
            aa['referenceassessments'] = [
                {
                    'allele_id': allele_id,
                    'reference_id': 43248,
                    'user_id': 1,
                    'evaluation': {
                        'comment': 'Some comment'
                    },
                    'analysis_id': 1
                }
            ]

            # POST data
            r = client.post('/api/v1/alleleassessments/', aa)

            # Check response
            assert r.status_code == 200
            aa = r.json[0]
            assert len(aa['referenceassessments']) == 1
            assert 'id' in aa['referenceassessments'][0]
            assert aa['referenceassessments'][0]['allele_id'] == allele_id
            assert aa['allele_id'] == allele_id
            assert aa['id'] == idx + 1

    @pytest.mark.aa(order=1)
    def test_update_assessment(self, client):
        """
        Simulate updating the AlleleAssessment created in create_new().
        It should result in a new AlleleAssessment being created,
        while the existing should be superceded.
        """

        interpretation = self._get_interpretation(client)

        q = {'allele_id': interpretation['allele_ids'], 'date_superceeded': None}
        previous_aa = client.get('/api/v1/alleleassessments/?q={}'.format(json.dumps(q))).json

        previous_ids = []
        for prev in previous_aa:
            # Prepare
            prev_id = prev['id']
            previous_ids.append(prev_id)
            # Delete the id, to make the backend create a new assessment
            del prev['id']
            prev['evaluation']['comment'] = "Some new comment"

            # Update referenceassessment
            prev_ra_id = prev['referenceassessments'][0]['id']
            del prev['referenceassessments'][0]['id']
            prev['referenceassessments'][0]['evaluation'] = {'comment': 'Some new comment'}

            # POST data
            r = client.post('/api/v1/alleleassessments/', prev)

            # Check response
            assert r.status_code == 200
            aa = r.json[0]
            assert aa['id'] != prev_id
            assert aa['evaluation']['comment'] == 'Some new comment'

            # Check that a new referenceassessment was created
            assert aa['referenceassessments'][0]['id'] != prev_ra_id
            assert aa['referenceassessments'][0]['evaluation']['comment'] == 'Some new comment'

        # Reload the previous alleleassessments and make sure
        # they're marked as superceded
        q = {'id': previous_ids}
        previous_aa = client.get('/api/v1/alleleassessments/?q={}'.format(json.dumps(q))).json

        assert all([p['date_superceeded'] is not None for p in previous_aa])

    @pytest.mark.aa(order=2)
    def test_fail_cases(self, client, testdata):
        """
        Test cases where it should fail to create assessments.
        """

        # Test without allele_id
        data = copy.deepcopy(testdata)
        del data['allele_id']

        # We don't run actual HTTP requests, everything is in python
        # so we can catch the exceptions directly
        with pytest.raises(ApiError):
            client.post('/api/v1/alleleassessments/', data)

        # Test without analysis_id
        data = copy.deepcopy(testdata)
        del data['analysis_id']

        with pytest.raises(ApiError):
            client.post('/api/v1/alleleassessments/', data)
