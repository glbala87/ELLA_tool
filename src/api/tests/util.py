import json
import os

from api import app
from api.main import api

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

    def __init__(self, url_prefix=''):
        app.testing = True
        api.init_app(app)
        self.app = app
        self.url_prefix = url_prefix
        self.cookie = None

    def set_cookie(self, client):
        def _set_cookie(cookie):
            cookie_name, cookie_value = cookie.split('=', 1)
            cookie_value = cookie_value.split(';')[0]
            client.set_cookie('localhost', cookie_name, cookie_value)

        if self.cookie is not None:
            _set_cookie(self.cookie)
        else:
            r = client.post("/api/v1/users/actions/login",
                            data=json.dumps({"username": "testuser1", "password": "ibsen123"}),
                            content_type='application/json')
            self.cookie = r.headers.get("Set-Cookie")
            _set_cookie(self.cookie)

    @json_out
    def get(self, url):
        with self.app.test_client() as client:
            self.set_cookie(client)
            return client.get(self.url_prefix + url, content_type='application/json')

    @json_out
    def post(self, url, data):
        with self.app.test_client() as client:
            self.set_cookie(client)
            return client.post(self.url_prefix + url, data=json.dumps(data), content_type='application/json')

    @json_out
    def put(self, url, data):
        with self.app.test_client() as client:
            self.set_cookie(client)
            return client.put(self.url_prefix + url, data=json.dumps(data), content_type='application/json')

    @json_out
    def patch(self, url, data):
        with self.app.test_client() as client:
            self.set_cookie(client)
            return client.patch(self.url_prefix + url, data=json.dumps(data), content_type='application/json')

    @json_out
    def delete(self, url, data):
        with self.app.test_client() as client:
            self.set_cookie(client)
            return client.delete(self.url_prefix + url, data=json.dumps(data), content_type='application/json')
