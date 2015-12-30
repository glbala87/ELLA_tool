import json
from flask import request
from api import db


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
