from pydantic import BaseModel
from fastapi import Depends, APIRouter, HTTPException
from fastapi.encoders import jsonable_encoder
from fastapi.security import OAuth2PasswordRequestForm
from starlette.responses import Response
from sqlalchemy.orm import Session

from api.depends import get_session
from api.util.useradmin import authenticate_user, create_session as create_user_session


router = APIRouter()


@router.post("/token")
def token(
    session: Session = Depends(get_session), form_data: OAuth2PasswordRequestForm = Depends()
):
    user = authenticate_user(session, form_data.username, form_data.password)
    if not user:
        raise HTTPException(status_code=400, detail="Incorrect username or password")
    token = create_user_session(session, user.id).decode()
    return {"access_token": token, "token_type": "bearer"}


class LoginIn(BaseModel):
    username: str
    password: str


@router.post("/login")
def login(login: LoginIn, session: Session = Depends(get_session)):
    user = authenticate_user(session, login.username, login.password)
    if not user:
        raise HTTPException(status_code=400, detail="Incorrect username or password")
    token = create_user_session(session, user.id).decode()
    r = Response("AUTHENTICATED", media_type="text/plain")
    r.set_cookie(
        "Authorization",
        jsonable_encoder(f"Bearer {token}"),
        expires=user.password_expiry,
        httponly=True,
    )
    return r

