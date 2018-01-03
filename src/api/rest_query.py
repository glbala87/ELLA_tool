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


class RestQuery(Query):

    def explain(self, analyze=False, print_json=False, stdout=True):
        """
        Prints EXPLAIN (ANALYZE) data to stdout to aid performance
        debugging.

        Call on query(), like session.query(...).filter(...).explain(analyze=True)
        The json option is for use with http://tatiyants.com/pev/
        """
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
