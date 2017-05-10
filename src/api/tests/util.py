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
        self.user_cookie = dict()  # Holds cookie tokens per user: {username: cookie}

    def is_logged_in(self, client):
        r = client.get("/api/v1/users/currentuser/")
        return r.status_code != 403

    def login(self, client, username):
        r = client.post("/api/v1/users/actions/login/",
                        data=json.dumps({"username": username, "password": "demo"}),
                        content_type='application/json')
        self.user_cookie[username] = r.headers.get("Set-Cookie")
        assert self.user_cookie[username] is not None

    def ensure_logged_in(self, client, username):

        def _set_client_cookie(client, cookie):
            cookie_name, cookie_value = cookie.split('=', 1)
            cookie_value = cookie_value.split(';')[0]
            client.set_cookie('localhost', cookie_name, cookie_value)

        if username in self.user_cookie:
            _set_client_cookie(client, self.user_cookie[username])

            # Check if session token is still valid
            if not self.is_logged_in(client):
                self.login(client, username)
        else:
            self.login(client, username=username)

        assert self.user_cookie[username] is not None
        _set_client_cookie(client, self.user_cookie[username])

    @json_out
    def get(self, url, username='testuser1'):
        with self.app.test_client() as client:
            if username:
                self.ensure_logged_in(client, username)
            return client.get(self.url_prefix + url, content_type='application/json')

    @json_out
    def post(self, url, data, username='testuser1'):
        with self.app.test_client() as client:
            if username:
                self.ensure_logged_in(client, username)
            return client.post(self.url_prefix + url, data=json.dumps(data), content_type='application/json')

    @json_out
    def put(self, url, data, username='testuser1'):
        with self.app.test_client() as client:
            if username:
                self.ensure_logged_in(client, username)
            return client.put(self.url_prefix + url, data=json.dumps(data), content_type='application/json')

    @json_out
    def patch(self, url, data, username='testuser1'):
        with self.app.test_client() as client:
            if username:
                self.ensure_logged_in(client, username)
            return client.patch(self.url_prefix + url, data=json.dumps(data), content_type='application/json')

    @json_out
    def delete(self, url, data, username='testuser1'):
        with self.app.test_client() as client:
            if username:
                self.ensure_logged_in(client, username)
            return client.delete(self.url_prefix + url, data=json.dumps(data), content_type='application/json')
