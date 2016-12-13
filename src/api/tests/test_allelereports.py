import json
import copy
import pytest

from util import FlaskClientProxy
from api import ApiError


def report_template(allele_id):
    return {
        "allele_id": allele_id,
        "analysis_id": 1,
        "user_id": 1,
        "classification": "1",
        "evaluation": {
            "comment": "Some comment",
        }
    }


@pytest.fixture
def client():
    return FlaskClientProxy()


class TestAlleleReports(object):

    def _get_interpretation_id(self, client):
        r = client.get('/api/v1/analyses/1/').json
        return r['interpretations'][0]['id']

    def _get_interpretation(self, client):
        return client.get('/api/v1/interpretations/{}/'.format(self._get_interpretation_id(client))).json

    @pytest.mark.ar(order=0)
    def test_create_new(self, test_database, client):
        test_database.refresh()  # Reset db

        # Create one AlleleReport for each allele in the interpretation:
        interpretation = self._get_interpretation(client)
        created_ids = list()
        for idx, allele_id in enumerate(interpretation['allele_ids']):

            # Prepare
            report_data = copy.deepcopy(report_template(allele_id))

            # POST data
            r = client.post('/api/v1/allelereports/', report_data)

            # Check response
            assert r.status_code == 200
            report_data = r.json[0]
            assert report_data['allele_id'] == allele_id
            assert report_data['id'] == idx + 1
            created_ids.append(report_data['id'])

        return created_ids

    @pytest.mark.ar(order=1)
    def test_create_new_and_reuse(self, test_database, client):
        # Create one AlleleReport for each allele in the interpretation:
        interpretation = self._get_interpretation(client)

        q = {'allele_id': interpretation['allele_ids'], 'date_superceeded': None}
        previous_reports = client.get('/api/v1/allelereports/?q={}'.format(json.dumps(q))).json
        previous_ids = []
        for report_data in previous_reports:
            prev_id = report_data['id']
            previous_ids.append(prev_id)  # bookkeeping

            report_data['id'] = 1  # The Api should discard this using @request_json
            report_data['reuse'] = True
            report_data['presented_report_id'] = prev_id

            # POST data
            r = client.post('/api/v1/allelereports/', report_data)

            # Check response
            assert r.status_code == 200
            new_report = r.json[0]
            assert new_report['allele_id'] == report_data['allele_id']
            assert new_report['id'] != prev_id

        # Reload the previous reports and make sure they're marked as superceded
        q = {'id': previous_ids}
        previous_reports = client.get('/api/v1/allelereports/?q={}'.format(json.dumps(q))).json

        assert all([p['date_superceeded'] is not None for p in previous_reports])

    @pytest.mark.ar(order=2)
    def test_update_reports(self, client):
        """
        Simulate updating the AlleleReport created in create_new().
        It should result in a new AlleleReport being created,
        while the existing should be superceded.
        """

        interpretation = self._get_interpretation(client)

        q = {'allele_id': interpretation['allele_ids'], 'date_superceeded': None}
        previous_aa = client.get('/api/v1/allelereports/?q={}'.format(json.dumps(q))).json

        previous_ids = []
        for prev in previous_aa:
            # Prepare
            prev_id = prev['id']
            previous_ids.append(prev_id)
            # Delete the id, to make the backend create a new report
            del prev['id']
            prev['evaluation']['comment'] = "Some new comment"

            # POST data
            r = client.post('/api/v1/allelereports/', prev)

            # Check response
            assert r.status_code == 200
            ar = r.json[0]
            # Check that the object is new
            assert ar['id'] != prev_id
            assert ar['evaluation']['comment'] == 'Some new comment'

        # Reload the previous allelereports and make sure
        # they're marked as superceded
        q = {'id': previous_ids}
        previous_aa = client.get('/api/v1/allelereports/?q={}'.format(json.dumps(q))).json

        assert all([p['date_superceeded'] is not None for p in previous_aa])


    @pytest.mark.ar(order=3)
    def test_fail_cases(self, client):
        """
        Test cases where it should fail to create reportss.
        """

        # Test without allele_id
        data = copy.deepcopy(report_template(999))
        del data['allele_id']

        # We don't run actual HTTP requests, everything is in python
        # so we can catch the exceptions directly
        with pytest.raises(ApiError):
            client.post('/api/v1/allelereports/', data)
