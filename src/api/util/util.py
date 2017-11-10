from functools import wraps
import json
import datetime
import pytz
import time
from flask import request, g, Response
from api import app, db, ApiError
from vardb.datamodel import user
from vardb.datamodel.log import ResourceLog
from sqlalchemy.orm import joinedload
from sqlalchemy.orm.scoping import scoped_session

log = app.logger

def query_print_table(sa_query):
    """
    Prints SQLAlchemy query as table to terminal.

    Used for debugging and adding examples to code comments.
    """
    column_names = [e['name'] for e in sa_query.column_descriptions]
    data = sa_query.all()
    column_width = {k: len(k) for k in column_names}
    for row in data:
        for name, cell in zip(column_names, row):
            cell_len = len(str(cell))
            if cell_len > column_width[name]:
                column_width[name] = cell_len

    h_divider = '-' * (sum(column_width.values()) + len(column_width) * 3)

    print h_divider
    row_format = '| '
    for name in column_names:
        row_format += '{:<' + str(column_width[name]) + '} | '

    print row_format.format(*column_names)

    print h_divider
    for r in data:
        print row_format.format(*r)

from vardb.datamodel import user


def error(msg, code):
    return {
        'error': msg,
        'status': code
    }, code


def rest_filter(func):

    @wraps(func)
    def inner(*args, **kwargs):
        q_filter = None
        if request:
            q = request.args.get('q')
            if q:
                q_filter = json.loads(q)

        return func(*args, rest_filter=q_filter, **kwargs)

    return inner

def search_filter(func):
    @wraps(func)
    def inner(*args, **kwargs):
        s_filter = None
        if request:
            s = request.args.get('s')
            if s:
                s_filter = json.loads(s)
        return func(*args, search_filter=s_filter, **kwargs)

    return inner


def link_filter(func):

    @wraps(func)
    def inner(*args, **kwargs):
        link_filter = None
        if request:
            link = request.args.get('link')
            if link:
                link_filter = json.loads(link)

        return func(*args, link_filter=link_filter, **kwargs)

    return inner

def log_request(statuscode, response=None):

    duration = int(time.time() * 1000.0 - g.request_start_time)
    remote_addr = request.remote_addr if not app.testing else '0.0.0.0'
    payload = None
    payload_size = 0
    response_data = None
    response_size = 0
    if response:
        response_size = response.headers.get('Content-Length')
        if not g.log_hide_response:
            response_data = response.get_data()
    if request.method in ['PUT', 'POST', 'PATCH', 'DELETE']:
        if not g.log_hide_payload:
            payload = request.get_data()
            payload_size = request.headers.get('Content-Length'),
        if not app.testing:  # don't add noise to console in tests, see tests.util.FlaskClientProxy
            log.warning("{usersession_id} - {method} - {endpoint} - {json} - {response_size}".format(
                usersession_id=g.usersession_id,
                method=request.method,
                endpoint=request.url,
                json=(payload if payload else '[PAYLOAD HIDDEN]'),
                response_size=response_size
            ))

    rl = ResourceLog(
        usersession_id=g.usersession_id,
        remote_addr=remote_addr,
        method=request.method,
        resource=request.path,
        query=request.query_string,
        response=response_data,
        response_size=response_size,
        payload=payload,
        payload_size=payload_size,
        statuscode=statuscode,
        duration=duration
    )
    db.session.add(rl)


def logger(hide_payload=False, hide_response=True):

    def _logger(func):
        @wraps(func)
        def inner(*args, **kwargs):
            g.log_hide_payload = hide_payload
            g.log_hide_response = hide_response
            return func(*args, **kwargs)

        return inner

    return _logger


def provide_session(func):

    @wraps(func)
    def inner(*args, **kwargs):
        try:
            return func(db.session, *args, **kwargs)
        except Exception:
            db.session.rollback()
            db.session.remove()
            raise
        finally:
            db.session.remove()

    return inner


def paginate(func):

    @wraps(func)
    def inner(*args, **kwargs):
        page = None
        if request:
            page = request.args.get('page')
        if page is None:
            page = 1
        else:
            page = int(page)
        num_per_page = None
        if request:
            num_per_page = request.args.get('num_per_page')
        if num_per_page is not None:
            num_per_page = int(num_per_page)
        else:
            num_per_page = 2000  # FIXME: Figure out the pagination stuff
        kwargs['page'] = page
        kwargs['num_per_page'] = num_per_page
        return func(*args, **kwargs)
    return inner


def request_json(required, only_required=False, allowed=None):
    """
    Decorator: Checks flasks's request (root) json object for 'required'
    fields before passing on the data to the function.

    If 'only_required', the json input is "washed" so only
    the fields in required are passed on.

    If 'allowed' is set, the json input is "washed" so only those fields are passed on.
    'allowed' accepts either an array ["field1", "field2" ..] or a dict ["top_key1": ["field",...], "top_key2": [...]}
    In the array case the array items tell which fields to keep in the root json object. In the dict case the array
    value of each key are used to filter the similar keyed object in the root json object.


    example:
    @request_json(["allele_id", "user_id"], allowed=["comment", "genepanel"])
    to filter an input like {"allele_id": 45, "user_id": 1, "illegal": 666, "comment": "important stuff"}

    or

    @request_json(["user", "content"], allowed={"user": ["user_id", "name"], "content": ["allele_id", "annotation"]})

    to filter an input like {"user":    {"id": 4, "name": "Erik", "address": "Parkveien"}
                             "content": {"mode": "weak", "allele_id": 34, "annotation": 44, "archived": true}}

    """

    # used by request_json to mutate an array of dicts
    def _check_array_content(source_array, required_fields, only_required=False, allowed_fields=None):
        for idx, d in enumerate(source_array):
            if required_fields:
                for field in required_fields:
                    if d.get(field) is None:
                        raise ApiError("Missing or empty required field {} in provided data.".format(field))

                if only_required:
                    source_array[idx] = {k: v for k, v in d.iteritems() if k in required_fields}
                elif allowed_fields:
                    source_array[idx] = {k: v for k, v in d.iteritems() if k in required_fields + allowed_fields}
            else:
                if allowed_fields:
                    source_array[idx] = {k: v for k, v in d.iteritems() if k in allowed_fields}

    def array_wrapper(func):

        @wraps(func)
        def inner(*args, **kwargs):
            data = request.get_json()
            if not isinstance(data, list):
                check_data = [data]
            else:
                check_data = data

            _check_array_content(check_data, required, only_required=only_required, allowed_fields=allowed)

            if not isinstance(data, list):
                data = check_data[0]
            else:
                data = check_data

            return func(*args, data=data, **kwargs)
        return inner

    def dict_wrapper(func):

        @wraps(func)
        def inner(*args, **kwargs):
            data = request.get_json()
            for data_key in data.keys():
                if required:
                    for fields in required:
                        if data.get(fields) is None:
                            raise ApiError("Missing or empty required field {} in provided data.".format(fields))

                if allowed:
                    assert isinstance(allowed, dict)
                    for allow_key in allowed.keys():
                        if allow_key == data_key:
                            _check_array_content(data[data_key], None, allowed_fields=allowed[allow_key])

            return func(*args, data=data, **kwargs)
        return inner

    if isinstance(allowed, dict):
        return dict_wrapper
    else:
        return array_wrapper


def _get_usersession_by_token(session, token):
    user_session = session.query(user.UserSession).options(joinedload("user")).filter(
        user.UserSession.token == token
    ).one_or_none()

    if user_session is None or \
       user_session.expires < datetime.datetime.now(pytz.utc) or \
       user_session.logged_out is not None:
        return None

    user_session.lastactivity = datetime.datetime.now(pytz.utc)
    session.commit()
    return user_session


def populate_g_user():
    g.user = None
    g.usersession_id = None
    token = request.cookies.get("AuthenticationToken")
    if token is None:
        return
    user_session = _get_usersession_by_token(db.session, token)
    if user_session:
        g.usersession_id = user_session.id
        g.user = user_session.user


def authenticate(user_role=None, user_group=None, optional=False):
    """
    Decorator that works in conjunction with flask's 'g' object
    in a before_request trigger, in order to auth the user as
    soon as request is processed.

    See populate_g_user().
    """
    def _authenticate(func):

        def _userHasAccess(session, token, user_role=None, user_group=None):
            if user_role is None and user_group is None:
                return True
            else:
                return False  # TODO: Implement user roles and user groups

        @wraps(func)
        def inner(*args, **kwargs):
            if g.user:
                # Logged in
                kwargs["user"] = g.user
                return func(*args, **kwargs)
            else:
                # Not logged in
                if optional:
                    return func(*args, **kwargs)
                else:
                    return Response("Authentication required", 403, {'WWWAuthenticate': 'Basic realm="Login Required"'})


        return inner
    return _authenticate


def get_nested(dct, *keys):
    if not dct or not isinstance(dct, dict):
        return None
    for i, key in enumerate(keys):
        try:
            dct = dct[key]
        except KeyError:
            return None
        if i == len(keys)-1:  # at end
            return dct
        if not isinstance(dct, dict):
            return None
    return None