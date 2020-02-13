from typing import Dict, Optional
import time
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.engine import Engine
from fastapi import Depends, FastAPI, HTTPException
from fastapi.security.utils import get_authorization_scheme_param
from starlette.authentication import AuthenticationBackend, AuthCredentials
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.middleware.authentication import AuthenticationMiddleware
from starlette.requests import Request
from starlette.status import HTTP_401_UNAUTHORIZED
from api.schemas.users import User


from api.util.useradmin import get_usersession_by_token
from .depends import get_current_user
from vardb.datamodel.log import ResourceLog
from api.v1.resources import config, auth, search


_db_conn: Optional[Engine] = None


def open_database_connection_pools():
    global _db_conn
    _db_conn = create_engine(os.environ.get("DB_URL"))


def close_database_connection_pools():
    global _db_conn
    if _db_conn:
        _db_conn.dispose()


async def create_session_middleware(request: Request, call_next):
    global _db_conn
    assert _db_conn is not None
    sess = Session(bind=_db_conn)
    request.state.db_session = sess
    try:
        response = await call_next(request)
    finally:
        request.state.db_session.close()
    return response


class OAuth2Backend(AuthenticationBackend):
    async def authenticate(self, request):
        header_authorization: str = request.headers.get("Authorization")
        cookie_authorization: str = request.cookies.get("Authorization")

        header_scheme, header_param = get_authorization_scheme_param(header_authorization)
        cookie_scheme, cookie_param = get_authorization_scheme_param(cookie_authorization)

        if header_scheme.lower() == "bearer":
            authorization = True
            scheme = header_scheme
            param = header_param

        elif cookie_scheme.lower() == "bearer":
            authorization = True
            scheme = cookie_scheme
            param = cookie_param
        else:
            authorization = False

        if not authorization or scheme.lower() != "bearer":
            return None, None
        else:
            usersession = get_usersession_by_token(request.state.db_session, param)
            if not usersession:
                raise HTTPException(
                    status_code=HTTP_401_UNAUTHORIZED,
                    detail="Invalid authentication credentials",
                    headers={"WWW-Authenticate": "Bearer"},
                )

            # The list in AuthCredentials is permissions.
            return AuthCredentials(["authenticated"]), usersession.user


async def resourcelog(request: Request, call_next):
    start = time.time()
    response = await call_next(request)
    duration = time.time() - start

    body = (await request.body()).decode()
    resp_len = int(next(r for r in response.raw_headers if r[0] == b"content-length")[1])
    current_usersession = getattr(request.state, "current_usersession", None)
    rl = ResourceLog(
        remote_addr=request.client.host,
        duration=duration,
        method=request.method,
        usersession_id=current_usersession.id if current_usersession else None,
        resource=request.url.path,
        query=request.scope["query_string"].decode(),
        payload=body,
        payload_size=len(body),
        statuscode=response.status_code,
        # FIXME: Get response content somehow or remove from log?
        # response=response.body,
        response_size=resp_len,
    )
    request.state.db_session.add(rl)
    request.state.db_session.commit()
    return response


app = FastAPI(openapi_url="/api/v1/openapi.json", docs_url="/api/v1/docs")
app.add_event_handler("startup", open_database_connection_pools)
app.add_event_handler("shutdown", close_database_connection_pools)

app.include_router(config.router, tags=["config"], prefix="/api/v1")
app.include_router(auth.router, tags=["auth"], prefix="/api/v1")
app.include_router(search.router, tags=["search"], prefix="/api/v1")

app.add_middleware(AuthenticationMiddleware, backend=OAuth2Backend())
app.add_middleware(BaseHTTPMiddleware, dispatch=resourcelog)
app.add_middleware(BaseHTTPMiddleware, dispatch=create_session_middleware)


@app.get("/api/v1/users/currentuser", response_model=User)
def get_current_user(user: User = Depends(get_current_user)):
    return user
