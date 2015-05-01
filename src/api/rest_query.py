from sqlalchemy import sql
from sqlalchemy.orm import Query
from sqlalchemy.orm.base import _entity_descriptor


OPERATORS = {
    # Operators which accept two arguments.
    '$eq': lambda f, a: f == a,
    '$neq': lambda f, a: f != a,
    '$gt': lambda f, a: f > a,
    '$lt': lambda f, a: f < a,
    '$gte': lambda f, a: f >= a,
    '$lte': lambda f, a: f <= a,
    '$in': lambda f, a: f.in_(a),
    '$nin': lambda f, a: ~f.in_(a),
}


class RestQuery(Query):

    def rest_filter(self, q):
        # based on filter_by() from sqlalchemy source

        clauses = list()

        for k, v in q.iteritems():
            field = _entity_descriptor(self._joinpoint_zero(), k)
            if isinstance(v, dict):
                for op_k, op_v in v.iteritems():
                    if op_k in OPERATORS:
                        clauses.append(OPERATORS[op_k](field, op_v))
            else:
                # Default is '=='
                clauses.append(field == v)

        return self.filter(sql.and_(*clauses))
