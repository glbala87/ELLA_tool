from __future__ import annotations

from typing import List

from api.schemas.pydantic.v1 import BaseModel
from api.schemas.pydantic.v1.genepanels import Genepanel


class User(BaseModel):
    id: int
    username: str
    first_name: str
    last_name: str
    full_name: str
    abbrev_name: str
    active: bool
    user_group_name: str


class UserGroup(BaseModel):
    id: int
    name: str
    genepanels: List[Genepanel]
    default_import_genepanel: Genepanel
    import_groups: List[str]


class UserFull(User):
    id: int
    username: str
    first_name: str
    last_name: str
    full_name: str
    email: str
    password_expiry: str
    active: bool
    group: UserGroup
