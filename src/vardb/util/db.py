import os
import sys


class DB(object):

    def __init__(self, host=None, pool_size=5, pool_max_overflow=10, pool_timeout=30):
        # Lazy load dependencies to avoid problems in code not actually using DB, but uses modules from which this module is referenced.
        from sqlalchemy import create_engine
        from sqlalchemy.orm import sessionmaker

        if not host:
            host = os.environ.get('DB_URL')
            if not host:
                # Keep backwards compatibility for now (but this should be changed!)
                if sys.platform.startswith('win'):
                    host = 'postgresql+psycopg2://vardb:heterozygous@localhost/vardb'
                else:
                    host = 'postgresql+psycopg2://localhost/vardb'
                # raise RuntimeError("Got no hostname as input and environment variable DB_URL is not set. Either set env, or fix the code.")

        self.host = host
        self.engine = create_engine(
            self.host,
            max_overflow=pool_max_overflow,
            pool_size=pool_size,
            pool_timeout=pool_timeout
        )
        self.sessionmaker = sessionmaker(bind=self.engine)  # Class for creating session instances
