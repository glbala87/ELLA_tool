from api.schemas.pydantic.v1 import BaseModel


class Broadcast(BaseModel):
    id: int
    date: str
    message: str