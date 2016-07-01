import pytest

from util import FlaskClientProxy


@pytest.fixture
def testdata():
    return {
        "allele_id": 1,
        "annotations": {
            "test": 1
        },
        "user_id": 1,
    }


@pytest.fixture
def client():
    return FlaskClientProxy()


class TestCustomAnnotation(object):

    @pytest.mark.ca(order=0)
    def test_create_new(self, test_database, testdata, client):
        test_database.refresh()  # Reset db

        # Insert new CustomAnnotation
        r = client.post('/api/v1/customannotations/', testdata)

        # Check that it's inserted
        r = client.get('/api/v1/customannotations/').json
        assert r[0]['annotations'] == testdata['annotations']
        assert r[0]['date_last_update']

    @pytest.mark.ca(order=1)
    def test_update_annotation_1(self, client, testdata):
        """
        Simulate updating CustomAnnotation.
        It should result in a new CustomAnnotation object being
        created, while the old one being superseded.
        """

        testdata['annotations'] = {'test': 2}
        r = client.post('/api/v1/customannotations/', testdata)

        # Check that it's inserted
        r = client.get('/api/v1/customannotations/').json
        assert r[1]['annotations'] == testdata['annotations']
        assert r[0]['date_superceeded']
        assert r[0]['annotations']['test'] == 1
        assert r[0]['id'] != r[1]['id']
