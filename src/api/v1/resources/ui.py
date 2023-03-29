from api.schemas.pydantic.v1 import validate_output
from api.schemas.pydantic.v1.resources import CreateExceptionLogRequest, EmptyResponse
from api.util.util import authenticate, request_json
from api.v1.resource import Resource
from sqlalchemy.orm import Session
from vardb.datamodel import log


class ExceptionLog(Resource):
    @authenticate(usersession=True, optional=True)
    @validate_output(EmptyResponse)
    @request_json(model=CreateExceptionLogRequest)
    def post(
        self, session: Session, data: CreateExceptionLogRequest, usersession_id: int, **kwargs
    ):
        new_exception = log.UiExceptionLog(
            usersession_id=usersession_id,
            message=data.message,
            location=data.location,
            stacktrace=data.stacktrace,
            state=data.state,
        )

        session.add(new_exception)
        session.commit()
