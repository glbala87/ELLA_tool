import subprocess
import json
import os

from api import app, db
from api.main import api

import vardb.datamodel


DB_PATH = os.path.join(
    os.path.dirname(os.path.realpath(__file__)),
    'testdata.psql'
)


def json_out(func):
    def wrapper(*args, **kwargs):
        r = func(*args, **kwargs)
        if r.data:
            try:
                r.json = json.loads(r.data)
            except ValueError:
                r.json = None
        else:
            r.json = None
        return r
    return wrapper


class FlaskClientProxy(object):

    def __init__(self):
        app.testing = True
        api.init_app(app)
        self.app = app

    @json_out
    def get(self, url):
        with self.app.test_client() as client:
            return client.get(url, content_type='application/json')

    @json_out
    def post(self, url, data):
        with self.app.test_client() as client:
            return client.post(url, data=json.dumps(data), content_type='application/json')

    @json_out
    def put(self, url, data):
        with self.app.test_client() as client:
            return client.put(url, data=json.dumps(data), content_type='application/json')

    @json_out
    def delete(self, url, data):
        with self.app.test_client() as client:
            return client.delete(url, data=json.dumps(data), content_type='application/json')


def reset_db():
    try:
        db.engine.dispose()
        subprocess.check_output('dropdb "vardb"'.format(DB_PATH), shell=True)
    except subprocess.CalledProcessError:
        pass
    subprocess.check_output('psql < {}'.format(DB_PATH), shell=True)
