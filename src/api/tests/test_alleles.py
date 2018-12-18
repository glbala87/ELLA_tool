import pytest
import json
from util import FlaskClientProxy


@pytest.fixture
def client():
    return FlaskClientProxy()


class TestAlleleList(object):
    """Test the response of /alleles endpoint"""

    # Maybe not a permanent test. Useful when changing unknown code base
    def test_get_alleles(self, client):

        # ids = [1, 2, 3, 4, 5, 6]
        ids = [1]
        q = {"id": ids}
        response = client.get("/api/v1/alleles/?q={}".format(json.dumps(q)))

        assert response.status_code == 200

        alleles = response.json
        assert len(alleles) == len(ids)
        assert "id" in alleles[0]
        for k in ["external", "frequencies", "references", "transcripts"]:
            assert k in alleles[0]["annotation"]
