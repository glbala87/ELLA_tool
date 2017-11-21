import json
from sqlalchemy import sql
from sqlalchemy.orm import Query
from sqlalchemy.orm.base import _entity_descriptor

from sqlalchemy.ext.compiler import compiles
from sqlalchemy.sql.expression import Executable, ClauseElement, _literal_as_text


class explain(Executable, ClauseElement):
    def __init__(self, stmt, analyze=False, json=False):
        self.statement = _literal_as_text(stmt)
        self.analyze = analyze
        self.json = json
        # helps with INSERT statements
        self.inline = getattr(stmt, 'inline', None)


@compiles(explain, 'postgresql')
def pg_explain(element, compiler, **kw):
    text = "EXPLAIN "
    if element.json:
        text += '(ANALYZE, COSTS, VERBOSE, BUFFERS, FORMAT JSON)'
    elif element.analyze:
        text += "ANALYZE "
    text += compiler.process(element.statement, **kw)
    return text


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

    def explain(self, analyze=False, print_json=False, stdout=True):
        explained = self.session.execute(explain(self, analyze=analyze, json=print_json)).fetchall()
        if stdout:
            print '''                                                       QUERY PLAN
---------------------------------------------------------------------------------------------------------------------------'''
            for e in explained:
                if json:
                    print json.dumps(e[0])
                else:
                    print ','.join(e)
        else:
            return explained
