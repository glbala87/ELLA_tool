import os
import subprocess
import tempfile
from sqlalchemy.pool import NullPool
from vardb.datamodel.annotationshadow import update_annotation_shadow_columns
from api import db
from api.config import config


class TestDatabase(object):
    def __init__(self):
        db_url = os.environ["DB_URL"]
        self.db_name = db_url.rsplit("/", 1)[-1]

        # Reconnect with NullPool in order to avoid hanging connections
        # which prevents us from dropping/creating database
        db.disconnect()
        db.connect(engine_kwargs={"poolclass": NullPool})
        subprocess.check_call("python /ella/ops/testdata/fetch-testdata.py".split())
        if not self.database_exists(self.db_name + "-template"):
            self.create_dump()

    def get_dump_path(self):
        with tempfile.NamedTemporaryFile() as tmpfile:
            return tmpfile.name

    def database_exists(self, db_name):
        # Check if database exists. This will throw an error if self.db_name doesn't exists, or
        # evalutate to None if {self.db_name}-template does not exist. If it does exist, then we
        # trust that it is up to date, and that we don't need to repopulate.
        try:
            if db.engine.execute(
                f"SELECT 1 from pg_database WHERE datname='{self.db_name}-template'"
            ).scalar():
                return True
        except:
            pass

        return False

    def create_dump(self):
        """
        Deposit testdata, and creates a dump of the test database into a template database to be used for refresh
        """

        with open(os.devnull, "w") as f:
            subprocess.check_call(f"dropdb --if-exists {self.db_name}", shell=True, stdout=f)
            subprocess.check_call(f"createdb {self.db_name}", shell=True, stdout=f)
            subprocess.check_call("ella-cli database drop -f", shell=True, stdout=f)
            subprocess.check_call("ella-cli database make -f", shell=True, stdout=f)
            if os.getenv("MIGRATION") == "1":
                print("Migration running")
                subprocess.call("ella-cli database ci-migration-head -f", shell=True)
                subprocess.call("ella-cli database refresh -f", shell=True, stdout=f)
            subprocess.check_call(
                "python /ella/ops/testdata/reset-testdata.py --testset integration_testing".split()
            )

            subprocess.check_call(f"dropdb --if-exists {self.db_name}-template", shell=True)
            subprocess.check_call(
                f"createdb {self.db_name}-template --template {self.db_name}", shell=True
            )
        print(f"Template database for testdata created in database {self.db_name}-template")

    def refresh(self):
        """
        Wipes out whole database, and recreates a clean copy from the template.
        """
        print("Refreshing database with data from template")
        if not self.database_exists(self.db_name + "-template"):
            self.create_dump()
        with open(os.devnull, "w") as f:
            subprocess.check_call(f"dropdb --if-exists {self.db_name}", shell=True, stdout=f)
            subprocess.check_call(
                f"createdb {self.db_name} --template {self.db_name}-template", shell=True, stdout=f
            )

        # Update mapping of annotation shadow tables based on global config
        update_annotation_shadow_columns(config)

    def cleanup(self):
        print("Disconnecting...")
        db.disconnect()
