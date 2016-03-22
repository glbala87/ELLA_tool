import json
from flask import request
from api import db, ApiError


def error(msg, code):
    return {
        'error': msg,
        'status': code
    }, code


def rest_filter(func):

    def inner(*args, **kwargs):
        q = request.args.get('q')
        rest_filter = None
        if q:
            rest_filter = json.loads(q)
        return func(*args, rest_filter=rest_filter, **kwargs)

    return inner


def provide_session(func):
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

    def inner(*args, **kwargs):
        page = request.args.get('page')
        if page is None:
            page = 1
        else:
            page = int(page)
        num_per_page = request.args.get('num_per_page')
        if num_per_page is not None:
            kwargs['num_per_page'] = int(num_per_page)
        else:
            num_per_page = 20
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
        def inner(*args, **kwargs):
            data = request.get_json()
            if not isinstance(data, list):
                check_data = [data]
            else:
                check_data = data
            for idx, d in enumerate(check_data):
                for field in required:
                    if not d.get(field):
                        raise ApiError("Missing or empty required field {} in provided data.".format(field))

                if only_required:
                    check_data[idx] = {k: v for k, v in d.iteritems() if k in required}
                elif allowed:
                    check_data[idx] = {k: v for k, v in d.iteritems() if k in required + allowed}
            if not isinstance(data, list):
                data = check_data[0]
            else:
                data = check_data
            return func(*args, data=check_data, **kwargs)
        return inner
    return wrapper
