from functools import wraps
import json
from flask import request
from api import db, ApiError


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
            kwargs['num_per_page'] = int(num_per_page)
        else:
            num_per_page = 2000  # FIXME: Figure out the pagination stuff
        kwargs['page'] = page
        kwargs['num_per_page'] = num_per_page
        return func(*args, **kwargs)
    return inner


def request_json(required, only_required=False, allowed=None):
    """
    Decorator: Checks flasks's request json object for 'required'
    fields before passing on the data to the function.

    If 'only_required', the json input is "washed" so only
    the fields in required are passed on.

    If 'allowed' is set, the json input is "washed" so only
    those fields are passed on.
    """
    def wrapper(func):

        @wraps(func)
        def inner(*args, **kwargs):
            data = request.get_json()
            if not isinstance(data, list):
                check_data = [data]
            else:
                check_data = data
            for idx, d in enumerate(check_data):
                if required:
                    for field in required:
                        if d.get(field) is None:
                            raise ApiError("Missing or empty required field {} in provided data.".format(field))

                    if only_required:
                        check_data[idx] = {k: v for k, v in d.iteritems() if k in required}
                    elif allowed:
                        check_data[idx] = {k: v for k, v in d.iteritems() if k in required + allowed}
                else:
                    if allowed:
                        check_data[idx] = {k: v for k, v in d.iteritems() if k in allowed}
            if not isinstance(data, list):
                data = check_data[0]
            else:
                data = check_data
            return func(*args, data=data, **kwargs)
        return inner
    return wrapper
