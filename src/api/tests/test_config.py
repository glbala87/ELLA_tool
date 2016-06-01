import copy
import pytest

from util import FlaskClientProxy


@pytest.fixture
def client():
    return FlaskClientProxy()


def test_config(client):
    r = client.get('/api/v1/config/')
    assert r.status_code == 200
    response_keys = r.json.keys()
    for k in ['frequencies', 'acmg', 'genepanel_default']:
        assert k in response_keys

