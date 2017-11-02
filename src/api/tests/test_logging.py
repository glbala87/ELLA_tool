import datetime
import pytest
import json
from vardb.util import DB
from vardb.datamodel import log

from util import FlaskClientProxy


@pytest.fixture
def client():
    return FlaskClientProxy()


def test_resourcelog(client):
    """
    Test that requests to the API are logged correctly in the 'requestloq' table.

    These tests are by default logged in as testuser1, with usersession_id of 1.
    """

    db = DB()
    db.connect()
    session = db.session()

    usersession_id = 1
    remote_addr = '0.0.0.0'  # Manually set in API code

    # Without payload
    r = client.get('/api/v1/config/')
    statuscode = r.status_code
    response_size = int(r.headers.get('Content-Length'))

    rlogs = session.query(log.ResourceLog).all()
    assert len(rlogs) == 2  # 2 entries since API did a login as first entry

    rl = rlogs[1]
    assert rl.remote_addr == remote_addr
    assert rl.usersession_id == usersession_id
    assert rl.method == 'GET'
    assert rl.resource == '/api/v1/config/'
    assert rl.statuscode == statuscode
    assert rl.response_size == response_size
    assert rl.payload == None
    assert rl.payload_size == 0
    assert rl.query == ''
    assert rl.duration > 0
    assert isinstance(rl.time, datetime.datetime)


    # With payload

    payload_data = {'allele_ids' : [1], 'gp_name': 'HBOCUTV', 'gp_version': 'v01', 'referenceassessments': []}
    r = client.post('/api/v1/acmg/alleles/?dummy=data', payload_data)
    payload = json.dumps(payload_data)
    payload_size = len(payload)
    statuscode = r.status_code
    response_size = int(r.headers.get('Content-Length'))

    rlogs = session.query(log.ResourceLog).all()
    assert len(rlogs) == 4  # 4 since /currentuser is called to check whether logged in

    rl = rlogs[3]
    assert statuscode == 200
    assert rl.remote_addr == remote_addr
    assert rl.usersession_id == usersession_id
    assert rl.method == 'POST'
    assert rl.resource == '/api/v1/acmg/alleles/'
    assert rl.statuscode == statuscode
    assert rl.response_size == response_size
    assert rl.payload == payload
    assert rl.payload_size == payload_size
    assert rl.query == 'dummy=data'
    assert rl.duration > 0
    assert isinstance(rl.time, datetime.datetime)


    # Make sure /login doesn't log passwords
    payload_data = {'username': 'abc', 'password': '123'}
    r = client.post('/api/v1/users/actions/login/', payload_data)
    statuscode = r.status_code
    response_size = int(r.headers.get('Content-Length'))

    rlogs = session.query(log.ResourceLog).all()
    assert len(rlogs) == 6  # 4 since /currentuser is called to check whether logged in

    rl = rlogs[5]
    assert statuscode == 401 # User doesn't exist
    assert rl.remote_addr == remote_addr
    assert rl.usersession_id == usersession_id
    assert rl.method == 'POST'
    assert rl.resource == '/api/v1/users/actions/login/'
    assert rl.statuscode == statuscode
    assert rl.response_size == response_size
    assert rl.payload == None
    assert rl.payload_size == 0
    assert rl.query == ''
    assert rl.duration > 0
    assert isinstance(rl.time, datetime.datetime)
