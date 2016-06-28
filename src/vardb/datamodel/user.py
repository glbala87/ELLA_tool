from sqlalchemy import Column, Sequence, Integer, String

from vardb.datamodel import Base


class User(Base):
    """Represents an assessment of one or more alleles."""
    __tablename__ = "user"

    id = Column(Integer, Sequence("id_user_seq"), primary_key=True)
    username = Column(String(), nullable=False)
    first_name = Column(String(), nullable=False)
    last_name = Column(String(), nullable=False)
