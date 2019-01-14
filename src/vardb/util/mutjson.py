"""Implements JSONB and ARRAY types with mutation tracking

Adapted from https://gist.github.com/kageurufu/7108738
but fixed to not turn strings into character lists.

Requires the use of postgresql and psycopg2.
Should be tested and understood more deeply (how functions are called is somewhat 'magic').
"""

import collections

from sqlalchemy.dialects import postgresql
from sqlalchemy.ext.mutable import MutableDict, Mutable


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
