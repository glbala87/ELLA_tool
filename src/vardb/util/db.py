import os
import re
import json
from sqlalchemy.orm import scoped_session
from .extended_query import ExtendedQuery
import jsonschema


class DB(object):
    def __init__(self):
        self.engine = None
        self.session = None

    def connect(self, host=None, engine_kwargs=None):

        # Lazy load dependencies to avoid problems in code not actually using DB, but uses modules from which this module is referenced.
        from sqlalchemy import create_engine, event
        from sqlalchemy.orm import sessionmaker

        # Disconnect in case we're already connected
        self.disconnect()
        self.host = host or os.environ.get("DB_URL")

        if not engine_kwargs:
            engine_kwargs = dict()

        self.engine = create_engine(self.host, client_encoding="utf8", **engine_kwargs)

        self.sessionmaker = sessionmaker(  # Class for creating session instances
            bind=self.engine, query_cls=ExtendedQuery
        )
        self.session = scoped_session(self.sessionmaker)

        # Error handling. Extend if required.
        @event.listens_for(self.engine, "handle_error")
        def handle_exception(context):
            if context.original_exception.pgcode != "JSONV":
                raise
            else:
                # We handle only one error in python, as the error raised by json validation is very limited in information.
                # Create a more meaningful error message with jsonschema here.
                from sqlalchemy.orm import sessionmaker
                from vardb.datamodel.jsonschemas.jsonvalidationerror import (
                    concatenate_json_validation_errors,
                    JSONValidationError,
                )

                message = context.original_exception.diag.message_primary
                message_data = message.split(" ---- ")[0]
                m = re.match("schema_name=([^,]*), data=(.*)", message_data)
                if not m:
                    raise
                else:
                    schema_name, data = m.groups()
                    data = json.loads(data)
                    session = scoped_session(
                        sessionmaker(bind=context.engine, query_cls=ExtendedQuery)
                    )
                    error_message = concatenate_json_validation_errors(session, data, schema_name)
                    raise JSONValidationError(error_message)

    def disconnect(self):
        if self.session:
            self.session.close()
        if self.engine:
            self.engine.dispose()
