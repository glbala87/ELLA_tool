from __future__ import annotations

from pydantic import Field
from typing import Dict
from api.schemas.pydantic.v1 import BaseModel


class ExceptionLog(BaseModel):
    id: int
    time: str
    usersession_id: int
    message: str
    location: str
    stacktrace: str
    state: Dict = Field(default_factory=dict)
