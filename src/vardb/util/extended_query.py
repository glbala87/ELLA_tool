import json
import random
import string
from sqlalchemy import table
from sqlalchemy.sql import text
from sqlalchemy.orm import Query

from sqlalchemy.ext.compiler import compiles
from sqlalchemy.sql.expression import Executable, ClauseElement, _literal_as_text

import logging

logger = logging.getLogger(__name__)


class CreateTempTableAs(Executable, ClauseElement):
    def __init__(self, name, query):
        self.name = name
        self.query = query.statement


@compiles(CreateTempTableAs, "postgresql")
def _create_temp_table_as(element, compiler, **kw):
    return "CREATE TEMP TABLE %s ON COMMIT DROP AS %s" % (
        element.name,
        compiler.process(element.query),
    )


class explain(Executable, ClauseElement):
    def __init__(self, stmt, analyze=False, json=False):
        self.statement = _literal_as_text(stmt)
        self.analyze = analyze
        self.json = json
        # helps with INSERT statements
        self.inline = getattr(stmt, "inline", None)


@compiles(explain, "postgresql")
def pg_explain(element, compiler, **kw):
    text = "EXPLAIN "
    if element.json:
        text += "(ANALYZE, COSTS, VERBOSE, BUFFERS, FORMAT JSON)"
    elif element.analyze:
        text += "ANALYZE "
    text += compiler.process(element.statement, **kw)
    return text


class ExtendedQuery(Query):
    def explain(self, analyze=False, print_json=False, stdout=True):
        """
        Prints EXPLAIN (ANALYZE) data to stdout to aid performance
        debugging.

        Call on query(), like session.query(...).filter(...).explain(analyze=True)
        The json option is for use with http://tatiyants.com/pev/
        """
        explained = self.session.execute(explain(self, analyze=analyze, json=print_json)).fetchall()
        if stdout:
            print(
                """                                                       QUERY PLAN
---------------------------------------------------------------------------------------------------------------------------"""
            )
            for e in explained:
                if json:
                    print(json.dumps(e[0]))
                else:
                    print(",".join(e))
        else:
            return explained

    def sql_statement(self):
        """
        Returns the SQL statement of the query that can be executed directly in psql.
        """
        return str(self.statement.compile(compile_kwargs={"literal_binds": True}))

    def temp_table(self, name, analyze=True, index=None):
        """
        Creates a ON COMMIT DROP temporary table from query with provided name.

        name is prefixed with 'tmp_table' and a random hash to avoid name clashing, e.g.
        tmp_table_edomlfph_<name>

        :warning: name is not escaped.

        Returns table() structure of query.

        If database user does not have write-access, this will return self.subquery(name)
        """
        has_write_access = self.session.execute(
            "SELECT * FROM pg_catalog.has_schema_privilege(current_user, 'public', 'CREATE')"
        ).scalar()

        if not has_write_access:
            logger.warning(
                "User does not have write access on schema 'public'. Will not create temp table."
            )
            return self.subquery(name)

        prefix = "".join(random.choice(string.ascii_lowercase) for _ in range(8))

        name = "tmp_table_" + prefix + "_" + name
        self.session.execute(text("DROP TABLE IF EXISTS {}".format(name)))
        self.session.execute(CreateTempTableAs(name, self))

        if analyze:
            self.session.execute(text("ANALYZE {}".format(name)))

        if index:
            for i in index:
                self.session.execute(text(f"CREATE INDEX idx_{prefix}_{i} ON {name} ({i})"))

        return table(name, *[c for c in self.subquery().columns])

    def scalar_all(self):
        return [a[0] for a in self.all()]
