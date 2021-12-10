from api.schemas.pydantic.v1 import BaseModel


class Comment(BaseModel):
    comment: str


class SearchFilter(BaseModel):
    search_string: str
