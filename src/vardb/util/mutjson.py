"""Implements JSONB and ARRAY types with mutation tracking

Adapted from https://gist.github.com/kageurufu/7108738
but fixed to not turn strings into character lists.

Requires the use of postgresql and psycopg2.
Should be tested and understood more deeply (how functions are called is somewhat 'magic').
"""

import collections

from sqlalchemy.dialects import postgresql
from sqlalchemy.dialects.postgresql.base import ischema_names, PGTypeCompiler
from sqlalchemy import types as sqltypes
from sqlalchemy.sql import functions as sqlfunc
from sqlalchemy.sql.operators import custom_op
from sqlalchemy import util

from json import dumps as dumpjson
from sqlalchemy.ext.mutable import MutableDict, Mutable


__all__ = ['MUTJSONB', 'mutjsonb']


class MUTJSONB(sqltypes.Concatenable, sqltypes.TypeEngine):
    """Represents the Postgresql JSON type.

    The :class:`.JSON` type stores python dictionaries using standard
    python json libraries to parse and serialize the data for storage
    in your database.
    """

    __visit_name__ = 'MUTJSONB'

    class comparator_factory(sqltypes.Concatenable.Comparator):

        def __getitem__(self, other):
            '''Gets the value at a given index for an array.'''
            return self.expr.op('->>')(other)

        def get_array_item(self, other):
            return self.expr.op('->')(other)

        def _adapt_expression(self, op, other_comparator):
            if isinstance(op, custom_op):
                if op.opstring in ['->', '#>']:
                    return op, sqltypes.Boolean
                elif op.opstring in ['->>', '#>>']:
                    return op, sqltypes.String
            return sqltypes.Concatenable.Comparator. \
                _adapt_expression(self, op, other_comparator)

    def bind_processor(self, dialect):
        if util.py2k:
            encoding = dialect.encoding

        def process(value):
            if value is not None:
                return dumpjson(value)
            return value

        return process

    def result_processor(self, dialect, coltype):
        return lambda v: v


ischema_names['jsonb'] = MUTJSONB


class mutjsonb(sqlfunc.GenericFunction):
    type = MUTJSONB
    name = 'to_jsonb'


class _MUTJSONBFunction(sqlfunc.GenericFunction):
    type = sqltypes.Integer
    name = 'jsonb_array_length'


class _MUTJSONBExtractPathFunction(sqlfunc.GenericFunction):
    type = MUTJSONB
    name = 'jsonb_extract_path'


class _MUTJSONBExtractPathTestFunction(sqlfunc.GenericFunction):
    type = sqltypes.String
    name = 'jsonb_extract_path_test'


PGTypeCompiler.visit_MUTJSONB = lambda self, type_: 'JSONB'


class JSONMutableDict(MutableDict):
    def __setitem__(self, key, value):
        if isinstance(value, collections.Mapping):
            if not isinstance(value, JSONMutableDict):
                value = JSONMutableDict.coerce(key, value)
        elif isinstance(value, list):
            value = JSONMutableList.coerce(key, value)
        dict.__setitem__(self, key, value)
        self.changed()

    def __getitem__(self, key):
        value = dict.__getitem__(self, key)
        if isinstance(value, dict):
            if not isinstance(value, JSONMutableDict):
                value = JSONMutableDict.coerce(key, value)
                value._parents = self._parents
                dict.__setitem__(self, key, value)
                return value
        elif isinstance(value, list):
            value = JSONMutableList.coerce(key, value)
            value._parents = self._parents
        dict.__setitem__(self, key, value)
        return value

    @classmethod
    def coerce(cls, key, value):
        """Convert plain dictionary to JSONMutableDict."""
        if not isinstance(value, JSONMutableDict):
            if isinstance(value, dict):
                return JSONMutableDict(value)
            return Mutable.coerce(key, value)
        else:
            return value


class MutableList(Mutable, list):
    def __setitem__(self, key, value):
        list.__setitem__(self, key, value)
        self.changed()

    def __delitem__(self, key):
        list.__delitem__(self, key)
        self.changed()

    def __setslice__(self, i, j, sequence):
        list.__setslice__(self, i, j, sequence)
        self.changed()

    def __delslice__(self, i, j):
        list.__delslice__(self, i, j)
        self.changed()

    def extend(self, iterable):
        list.extend(self, iterable)
        self.changed()

    def insert(self, index, p_object):
        list.insert(self, index, p_object)
        self.changed()

    def append(self, p_object):
        list.append(self, p_object)
        self.changed()

    def pop(self, index=None):
        list.pop(self, index)
        self.changed()

    def remove(self, value):
        list.remove(self, value)
        self.changed()

    @classmethod
    def coerce(cls, key, value):
        if not isinstance(value, MutableList):
            if isinstance(value, collections.Iterable):
                return MutableList(value)
            return Mutable.coerce(key, value)
        return value


class JSONMutableList(MutableList):
    def __setitem__(self, key, value):
        if isinstance(value, collections.Mapping):
            if not isinstance(value, JSONMutableDict):
                value = JSONMutableDict(value)
        elif isinstance(value, list):
            value = JSONMutableList(value)
        list.__setitem__(self, key, value)
        self.changed()

    def __getitem__(self, key):
        value = super(JSONMutableList, self).__getitem__(key)
        if isinstance(value, collections.Mapping):
            if not isinstance(value, JSONMutableDict):
                value = JSONMutableDict.coerce(key, value)
                value._parents = self._parents
                list.__setitem__(self, key, value)
        elif isinstance(value, list):
            value = JSONMutableList.coerce(key, value)
            value._parents = self._parents
        list.__setitem__(self, key, value)
        return value

    @classmethod
    def coerce(cls, key, value):
        if not isinstance(value, JSONMutableList):
            if isinstance(value, list):
                return JSONMutableList(value)
            return Mutable.coerce(key, value)
        return value


MutableList.associate_with(postgresql.ARRAY)
JSONMutableDict.associate_with(MUTJSONB)
