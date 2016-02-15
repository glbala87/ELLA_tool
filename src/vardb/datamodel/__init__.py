import os
from vardb.util import DB
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm.exc import NoResultFound
from sqlalchemy.orm.session import Session as SessionType


class CustomBase(object):

    @classmethod
    def get_or_create(cls, session, defaults=None, **kwargs):
        """
        Clone of Django's equivalent function.
        Looks up an object with the given kwargs, creating one if necessary.
        If an object is created, defaults are applied to object.
        Returns a tuple of (object, created), where created is a boolean
        specifying whether an object was created.
        """
        instance = session.query(cls).filter_by(**kwargs).first()
        # Facilitate mock testing by creating new object if session is mocked.
        if isinstance(instance, cls) and instance:
            return instance, False
        else:
            params = dict(kwargs)
            params.update(defaults or {})
            instance = cls(**params)
            try:
                session.add(instance)
                session.flush()
                return instance, True
            # Avoid concurrency problems, if an object
            # is inserted by another process between query and flush
            except IntegrityError as e:
                session.rollback()
                try:
                    # If there's no result, then we probably had a real integrity error
                    return session.query(cls).filter_by(**kwargs).one(), False
                except NoResultFound:
                    raise e


    @classmethod
    def update_or_create(cls, session, defaults=None, **kwargs):
        """
        Clone of Django's equivalent function.
        Looks up an object with the given kwargs, updating one with defaults
        if it exists, otherwise creates a new one.
        Returns a tuple (object, created), where created is a boolean
        specifying whether an object was created.
        """
        # get or create object using kwargs (filter) only
        instance, created = cls.get_or_create(session, **kwargs)
        # Update object with defaults
        if defaults:
            for k, v in defaults.iteritems():
                setattr(instance, k, v)
        return instance, created


Base = declarative_base(cls=CustomBase) # NB! Use this Base instance always.

# Don't remove:
from vardb.datamodel import allele, annotation, sample, assessment, genotype, gene, user
