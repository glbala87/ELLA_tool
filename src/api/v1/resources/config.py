from typing import Optional
import copy
from fastapi import Depends, APIRouter
from api.config import config as app_config, get_user_config

from api.schemas.users import User
from api.depends import get_current_user_optional

router = APIRouter()


@router.get("/config")
def config(user: Optional[User] = Depends(get_current_user_optional),):
    c = copy.deepcopy(app_config)
    if user:
        c["user"]["user_config"] = get_user_config(app_config, user.group.config, user.config)
    return c
