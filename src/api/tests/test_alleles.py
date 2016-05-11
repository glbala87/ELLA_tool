import json
import pytest

from util import FlaskClientProxy


@pytest.fixture
def client():
    return FlaskClientProxy()

class TestAlleleList(object):

    # Maybe not a permanent test. Useful when changing unknown code base
    def test_getAlleles(self, client, test_database):
        test_database.refresh()  # Reset db

        q = {"id": [1, 2, 3, 4, 5, 6]}
        response = client.get('/api/v1/alleles/?q={}'.format(json.dumps(q)))

        assert response.status_code == 200

        alleles = response.json
        assert len(alleles) == len(q['id'])
        assert 'id' in alleles[0]
        for k in ['external', 'frequencies', 'references', 'transcripts']:
            assert k in alleles[0]['annotation']


