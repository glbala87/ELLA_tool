from api.schemas.pydantic.v1 import BaseModel
from pydantic import Extra


class Comment(BaseModel):
    comment: str


class SearchFilter(BaseModel):
    search_string: str


class GenericID(BaseModel):
    id: int

    class Config(BaseModel.Config):
        extra = Extra.ignore
