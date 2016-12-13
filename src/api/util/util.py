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




def request_json(required, only_required=False, allowed=None, allowed_dict=None, only_required_dict=None):
    """
    Decorator: Checks flasks's request json object for 'required'
    fields before passing on the data to the function.

    If 'only_required', the json input is "washed" so only
    the fields in required are passed on.

    If 'allowed' is set, the json input is "washed" so only
    those fields are passed on.

    If 'allowed_dict' is set, the specified key(s) of the json input is "washed" similar to the 'allowed' keyword
    It's currently not possible to specify the required keys of the these dicts, thus only_required flag is not possible

    """

    # used by request_json to mutate an array of dicts
    def _check_and_filter(source_array, required_fields, only_required=False, allowed_fields=None):
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

    if allowed and allowed_dict:
        raise ApiError("Only one of 'allowed' and 'allowed_dict' can be configured")

    def array_wrapper(func):

        @wraps(func)
        def inner(*args, **kwargs):
            data = request.get_json()
            if not isinstance(data, list):
                check_data = [data]
            else:
                check_data = data

            _check_and_filter(check_data, required, only_required=only_required, allowed_fields=allowed)

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
                    for f in required:
                        if data.get(f) is None:
                            raise ApiError("Missing or empty required field {} in provided data.".format(f))

                if allowed_dict:
                    for allow_key in allowed_dict.keys():
                        if allow_key == data_key:
                            _check_and_filter(data[data_key], None, allowed_fields=allowed_dict[allow_key])

            return func(*args, data=data, **kwargs)
        return inner

    if allowed_dict:
        return dict_wrapper
    else:
        return array_wrapper
