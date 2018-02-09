import pytest
import json
from util import FlaskClientProxy

@pytest.fixture
def client():
    return FlaskClientProxy()

@pytest.mark.parametrize(("query,expected_analysis_ids,expected_allele_ids"), [
    ({"freetext": "brca_sample"}, [2,3,4], []),
    ({"freetext": "c.12"}, [], [18, 24]),
    ({"freetext": "c.12", "filter": True}, [], [24]), # allele id 18 should be filtered out
    ({"freetext": "p.glu"}, [], [12,14,15,17]),
    ({"freetext": "13:32890607"}, [], [1]),
    ({"freetext": "13:32890607-32890650"}, [], [1,2,3]),
])
def test_search(client, query, expected_analysis_ids, expected_allele_ids):
    response = client.get('/api/v1/search/?q={}'.format(json.dumps(query)))

    allele_ids = [a["id"] for a in response.json["alleles"]]
    analysis_ids = [a["id"] for a in response.json["analyses"]]

    assert set(allele_ids) == set(expected_allele_ids)
    assert set(analysis_ids) == set(expected_analysis_ids)
