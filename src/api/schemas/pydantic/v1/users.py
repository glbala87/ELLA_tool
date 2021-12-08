from __future__ import annotations

from typing import Dict, List

from api.schemas.pydantic.v1 import BaseModel


class User(BaseModel):
    id: int
    username: str
    first_name: str
    last_name: str
    full_name: str
    abbrev_name: str
    active: bool
    user_group_name: str


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


class UserGroup(BaseModel):
    id: int
    name: str
    genepanels: List[Dict]  # TODO: List[GenePanel], but circular imports causing problems
    default_import_genepanel: Dict  # TODO: GenePanel
