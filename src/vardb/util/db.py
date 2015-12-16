import os
import sys


class DB(object):

    def __init__(self, host=None, pool_size=5, pool_max_overflow=10, pool_timeout=30, query_cls=None):
        # Lazy load dependencies to avoid problems in code not actually using DB, but uses modules from which this module is referenced.
        from sqlalchemy import create_engine
        from sqlalchemy.orm import sessionmaker

        host = host or os.environ.get('DB_URL')

        if not host:
            if os.getenv('DB_PORT_5432_TCP_ADDR'):
                host = 'postgres://postgres@{0}/postgres'.format(os.getenv('DB_PORT_5432_TCP_ADDR'))
            else:
                host = 'postgresql+psycopg2://localhost/vardb'

        self.host = host
        self.engine = create_engine(
            self.host,
            max_overflow=pool_max_overflow,
            pool_size=pool_size,
            pool_timeout=pool_timeout
        )
        args = {
            'bind': self.engine
        }
        if query_cls:
            args.update({'query_cls': query_cls})
        self.sessionmaker = sessionmaker(**args)  # Class for creating session instances
