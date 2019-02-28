from sqlalchemy import Column, Integer, String
from sqlalchemy.dialects.postgresql import JSONB

from vardb.util.mutjson import JSONMutableDict
from vardb.datamodel import Base


class JSONSchema(Base):
    """Table for all JSON schemas used in the application"""

    __tablename__ = "jsonschema"

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    version = Column(Integer, nullable=False)
    schema = Column(JSONMutableDict.as_mutable(JSONB))

    def __repr__(self):
        return "<JSONSchema('%s', '%s')>" % (self.name, self.version)
