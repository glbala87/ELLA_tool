from __future__ import annotations

from typing import Optional

from api.schemas.pydantic.v1 import BaseModel
from api.schemas.pydantic.v1.users import User


class Attachment(BaseModel):
    id: int
    sha256: Optional[str] = None
    filename: str
    size: int
    date_created: str
    mimetype: Optional[str] = None
    extension: str
    thumbnail: Optional[str] = None
    user: User
