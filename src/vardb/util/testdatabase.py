import os
import subprocess
import tempfile
from sqlalchemy.pool import NullPool
from vardb.deposit.deposit_testdata import DepositTestdata
from vardb.datamodel.annotationshadow import update_annotation_shadow_columns
from api import db
from api.config import config


class TestDatabase(object):
    def __init__(self):
        self.dump_path = os.getenv("TEST_DB_DUMP")
        if not self.dump_path:
            self.dump_path = self.get_dump_path()

        # Reconnect with NullPool in order to avoid hanging connections
        # which prevents us from dropping/creating database
        db.disconnect()
        db.connect(engine_kwargs={"poolclass": NullPool})
        self.create_dump()

    def get_dump_path(self):
        with tempfile.NamedTemporaryFile() as tmpfile:
            return tmpfile.name

    def create_dump(self):
        """
        Creates a dump of the test database into file specified in self.dump_path.
        """
        if os.environ.get("TEST_DB_DUMP") and os.path.exists(os.environ.get("TEST_DB_DUMP")):
            return
        with open(os.devnull, "w") as f:
            db_url = os.environ["DB_URL"]
            db_name = db_url.rsplit("/", 1)[-1]
            subprocess.check_call(f"dropdb --if-exists {db_name}", shell=True, stdout=f)
            subprocess.check_call(f"createdb {db_name}", shell=True, stdout=f)
            subprocess.check_call("ella-cli database drop -f", shell=True, stdout=f)
            subprocess.check_call("ella-cli database make -f", shell=True, stdout=f)
            if os.getenv("MIGRATION") == "1":
                print("Migration running")
                subprocess.call("ella-cli database ci-migration-head -f", shell=True)
                subprocess.call("ella-cli database refresh -f", shell=True, stdout=f)
        DepositTestdata(db).deposit_all(test_set="integration_testing")

        # Note the --clean and --create flags, which will recreate db when run
        subprocess.check_call(
            "pg_dump {uri} --file={path} --clean --create".format(
                uri=os.environ["DB_URL"], path=self.dump_path
            ),
            shell=True,
        )
        print("Temporary database file created at {}.".format(self.dump_path))

    def refresh(self):
        """
        Wipes out whole database, and recreates a clean copy from the dump.
        """
        print("Refreshing database with data from dump")
        if not os.path.exists(self.dump_path):
            self.create_dump()

        with open(os.devnull, "w") as f:

            # Connect to template1 so we can remove whatever db name
            subprocess.check_call(
                "psql postgresql:///template1 < {path}".format(path=self.dump_path),
                shell=True,
                stdout=f,
            )

        # Update mapping of annotation shadow tables based on global config
        update_annotation_shadow_columns(config)

    def cleanup(self):
        print("Disconnecting...")
        db.disconnect()
        if os.getenv("TEST_DB_DUMP") != self.dump_path:
            try:
                os.remove(self.dump_path)
                print("Temporary database file removed.")
            except OSError:
                pass
