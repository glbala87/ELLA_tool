# -*- coding: latin1 -*-
from api.util.util import provide_session, logger
from flask.ext.restful import Resource as flask_resource
import sqlalchemy
from sqlalchemy import tuple_

FILTER_OPERATORS = {
    # Operators which accept two arguments.
    '$eq': lambda f, a: f == a,
    '$neq': lambda f, a: f != a,
    '$gt': lambda f, a: f > a,
    '$lt': lambda f, a: f < a,
    '$gte': lambda f, a: f >= a,
    '$lte': lambda f, a: f <= a,
    '$in': lambda f, a: f.in_(a),
    '$nin': lambda f, a: ~f.in_(a),
    '$like': lambda f, a: f.like("%"+a+"%"),
    '$ilike': lambda f, a: f.ilike("%"+a+"%"),
}


class Resource(flask_resource):

    method_decorators = [logger(hide_payload=True), provide_session]

    def _filter(self, query, model, rest_filter):
        args = list()
        for k, v in rest_filter.iteritems():
            if isinstance(v, list):
                operator = FILTER_OPERATORS['$in']
                if v:  # Asking for empty list doesn't make sense
                    if isinstance(k, tuple):
                        args.append(operator(tuple_(*(getattr(model, _k) for _k in k)), v))
                    else:
                        args.append(operator(getattr(model, k)), v)
            elif isinstance(v, dict):
                for op_k, op_v in v.iteritems():
                    args.append(FILTER_OPERATORS[op_k](getattr(model, k), op_v))
            else:
                args.append(FILTER_OPERATORS["$eq"](getattr(model, k), v))
        if args:
            query = query.filter(*args)
        return query

    def list_query(self, session, model, schema=None, **kwargs):
        query = session.query(model)
        if kwargs.get('rest_filter'):
            # Check if any of the requested filters are empty list, if so user has requested an empty
            # set so we should return nothing.
            # TODO: Review behavior
            if any((isinstance(v, list) and not v) for v in kwargs['rest_filter'].values()):
                return list(), 0
            query = self._filter(query, model, kwargs['rest_filter'])
        if kwargs.get('per_page'):
            query = query.limit(kwargs['per_page'])
        if kwargs.get('page') and kwargs.get('per_page'):
            query = query.offset((kwargs['page']-1)*kwargs['per_page'])
        count = query.count()
        s = query.all()
        if schema:
            result = schema.dump(s, many=True)
            return result.data, count
        else:
            return s, count

    def list_search(self, session, model, search_filter, schema=None, **kwargs):
        """Searches only full word matches
        Example: String to search in is 'breast and ovarian cancer'

        Match returned on:
        - breast
        - ovarian
        - breast and ovarian
        - breast and ovar
        - ovar and bre
        - breasts and ovarian

        Match not generally returned on misspelled words:
        - brxast

        However, match is returned on some misspellings:
        - ovariance

        The search string is cast to a tsquery by using plainto_tsquery, which returns
        - SELECT plainto_tsqeuery('breast and ovarian cancer') -> 'breast' & 'ovarian' & 'cancer'
        - SELECT plainto_tsquery('breasts and ovariance cancer'); ->  'breast' & 'ovari' & 'cancer'

        It is executed so that any word in the tsquery is matched with words prefixing, that is
        - 'ovari' matches 'ovarian'

        Possible improvements:
        - Use the similarity-function from the pg_trgm extension, so that e.g. 'stromberg' matches 'Str�hmberg'
        - Unaccent all input, so that e.g. 'strohmberg' matches 'Str�hmberg'
        """

        search_string = search_filter["search_string"]
        query = session.query(model)

        words = session.query(sqlalchemy.func.plainto_tsquery(search_string)).one()  # .statement.compile(compile_kwargs={"literal_binds": True})
        words = str(words[0])
        words = words.replace(" ", "").replace("'", "").replace('"', '').split("&")
        search_string = " & ".join([s+":*" for s in words])
        _search_vector = sqlalchemy.func.to_tsquery(sqlalchemy.text("'english'"), search_string)

        query = query.filter(model.search.op('@@')(_search_vector))
        query = query.order_by(sqlalchemy.func.ts_rank(model.search, _search_vector))

        if kwargs.get('per_page'):
            query = query.limit(kwargs["per_page"])
        if kwargs.get('page') and kwargs.get('per_page'):
            query = query.offset((kwargs['page'] - 1) * kwargs['per_page'])

        count = query.count()
        s = query.all()

        if schema:
            result = schema.dump(s, many=True)
            return result.data, count
        else:
            return s, count


class LogRequestResource(Resource):
    method_decorators = [logger(hide_payload=False), provide_session]
