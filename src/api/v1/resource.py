from api.util.util import provide_session
from flask.ext.restful import Resource as flask_resource


class Resource(flask_resource):

    method_decorators = [provide_session]

    def _filter(self, query, model, rest_filter):
        args = list()
        for k, v in rest_filter.iteritems():
            if isinstance(v, list):
                if v:  # Asking for empty list doesn't make sense
                    args.append(getattr(model, k).in_(v))
            else:
                args.append(getattr(model, k) == v)
        if args:
            query = query.filter(*args)
        return query

    def list_query(self, session, model, schema=None, **kwargs):
        query = session.query(model)
        if kwargs.get('rest_filter'):
            query = self._filter(query, model, kwargs['rest_filter'])
        if 'num_per_page' in kwargs:
            query = query.limit(kwargs['num_per_page'])
        if 'page' in kwargs and 'num_per_page' in kwargs:
            query = query.offset((kwargs['page']-1)*kwargs['num_per_page'])
        s = query.all()
        if schema:
            result = schema.dump(s, many=True)
            return result.data
        else:
            return s
