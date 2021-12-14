from vardb.datamodel import log
from api.v1.resource import Resource
from api.util.util import authenticate, request_json


class ExceptionLog(Resource):
    @authenticate(usersession=True, optional=True)
    @request_json(required_fields=["message", "location", "stacktrace", "state"])
    def post(self, session, data=None, user=None, usersession_id=None):
        new_exception = log.UiExceptionLog(
            usersession_id=usersession_id,
            message=data["message"],
            location=data["location"],
            stacktrace=data["stacktrace"],
            state=data["state"],
        )

        session.add(new_exception)
        session.commit()
