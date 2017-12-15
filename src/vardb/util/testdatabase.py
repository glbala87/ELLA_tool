import os
import subprocess
import tempfile
from sqlalchemy.pool import NullPool
from vardb.deposit.deposit_testdata import DepositTestdata
from api import db


class TestDatabase(object):

    def __init__(self):
        self.dump_path = self.get_dump_path()

        # Reconnect with NullPool in order to avoid hanging connections
        # which prevents us from dropping/creating database
        db.disconnect()
        db.connect(engine_kwargs={"poolclass": NullPool})
        self.create_dump()
        self.refresh()

    def get_dump_path(self):
        with tempfile.NamedTemporaryFile(delete=False) as tmpfile:
            return tmpfile.name

    def create_dump(self):
        """
        Creates a dump of the test database into file specified in self.dump_path.
        """
        if os.environ.get('TEST_DB_DUMP') and os.path.exists(os.environ.get('TEST_DB_DUMP')):
            return
        with open(os.devnull, "w") as f:
            subprocess.call('createdb {uri}'.format(uri=os.environ["DB_URL"]), shell=True, stdout=f)
        DepositTestdata(db).deposit_all(test_set='integration_testing')

        if os.environ.get('TEST_DB_DUMP'):
            dump_path = os.environ['TEST_DB_DUMP']
        else:
            dump_path = self.dump_path
        # Note the --clean and --create flags, which will recreate db when run
        subprocess.check_call('pg_dump {uri} --file={path} --clean --create'.format(uri=os.environ["DB_URL"], path=dump_path), shell=True)
        print "Temporary database file created at {}.".format(dump_path)

    def refresh(self):
        """
        Wipes out whole database, and recreates a clean copy from the dump.
        """
        print "Refreshing database with data from dump"

        if os.environ.get('TEST_DB_DUMP') and os.path.exists(os.environ.get('TEST_DB_DUMP')):
            dump_path = os.environ['TEST_DB_DUMP']
        else:
            dump_path = self.dump_path

        with open(os.devnull, "w") as f:
            # Connect to template1 so we can remove whatever db name
            subprocess.check_call('psql postgres://postgres@/template1 < {path}'.format(uri=os.environ["DB_URL"], path=dump_path), shell=True, stdout=f)

    def cleanup(self):
        print "Disconnecting..."
        db.disconnect()
        print "Removing database"
        subprocess.call('dropdb {uri}'.format(uri=os.environ["DB_URL"]), shell=True)
        try:
            os.remove(self.dump_path)
            print "Temporary database file removed."
        except OSError:
            pass
