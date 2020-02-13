from typing import Optional, AsyncIterable
import os
from starlette.status import HTTP_403_FORBIDDEN
from starlette.requests import Request
from fastapi import Depends, HTTPException
from sqlalchemy.orm import Session

from api.schemas.users import User


async def get_session(request: Request) -> AsyncIterable[Session]:
    return request.state.db_session


def get_current_user(request: Request) -> User:
    if "authenticated" not in request.auth.scopes or not request.user:
        raise HTTPException(status_code=HTTP_403_FORBIDDEN, detail="Not authenticated")
    return request.user


def get_current_user_optional(request: Request,) -> Optional[User]:
    return request.user
