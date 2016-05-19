import pytest
from util import FlaskClientProxy
from api.util.annotationprocessor.genepanelprocessor import BETWEEN_RESULT, BELOW_RESULT, ABOVE_RESULT


@pytest.fixture
def client():
    return FlaskClientProxy()


# Unicode version of str constants:
ABOVE_U = unicode(ABOVE_RESULT, 'utf-8')
BETWEEN_LOWER = unicode(BETWEEN_RESULT[0], 'utf-8')
BETWEEN_UPPER = unicode(BETWEEN_RESULT[1], 'utf-8')
BETWEEN_U = unicode(BELOW_RESULT, 'utf-8')

"""
Test the response of /alleles endpoint
"""
class TestAlleleList(object):

    # Maybe not a permanent test. Useful when changing unknown code base
    def test_get_alleles(self, client):

        ids = [1, 2, 3, 4, 5, 6]
        response = client.get('/api/v1/alleles/{}'.format(",".join(map(str,ids))))

        assert response.status_code == 200

        alleles = response.json
        assert len(alleles) == len(ids)
        assert 'id' in alleles[0]
        for k in ['external', 'frequencies', 'references', 'transcripts']:
            assert k in alleles[0]['annotation']


# Test that genepanel config overrides the default cutoff frequencies
@pytest.mark.parametrize("url, expected_1000g, expected_6500", [
    ('/api/v1/alleles/1?gp_name=HBOC&gp_version=v00', ABOVE_U, ABOVE_U),
    ('/api/v1/alleles/1', [BETWEEN_LOWER, BETWEEN_UPPER], BETWEEN_U)
])
def test_calculation_of_cutoffs(client, url, expected_1000g, expected_6500):
    response = client.get(url)
    assert response.status_code == 200

    alleles = response.json
    assert len(alleles) == 1

    our_allele = alleles[0]
    assert 1 == our_allele['id']

    frequency_annotations = our_allele['annotation']['frequencies']
    assert expected_1000g == frequency_annotations['1000G_cutoff']
    assert expected_6500 == frequency_annotations['ESP6500_cutoff']
