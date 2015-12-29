import os
import sys
from sqlalchemy.pool import NullPool
from sqlalchemy.orm import scoped_session


class DB(object):

    def __init__(self):
        self.engine = None

    def connect(self,
                host=None,
                engine_kwargs=None,
                query_cls=None):
        # Lazy load dependencies to avoid problems in code not actually using DB, but uses modules from which this module is referenced.
        from sqlalchemy import create_engine
        from sqlalchemy.orm import sessionmaker

        # Disconnect in case we're already connected
        self.disconnect()

        host = host or os.environ.get('DB_URL')

        if not host:
            if os.getenv('DB_PORT_5432_TCP_ADDR'):
                host = 'postgres://postgres@{0}/postgres'.format(os.getenv('DB_PORT_5432_TCP_ADDR'))
            else:
                host = 'postgresql+psycopg2://localhost/vardb'

        self.host = host

        if not engine_kwargs:
            engine_kwargs = dict()


        self.engine = create_engine(
            self.host,
            **engine_kwargs
        )
        args = {
            'bind': self.engine
        }
        if query_cls:
            args.update({'query_cls': query_cls})
        self.sessionmaker = sessionmaker(**args)  # Class for creating session instances
        self.session = scoped_session(self.sessionmaker)

    def disconnect(self):
        if self.engine:
            self.engine.dispose()
