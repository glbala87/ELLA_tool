import datetime
from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Boolean
from sqlalchemy.orm import relationship

from vardb.datamodel import Base


class User(Base):
    """Represents a user."""
    __tablename__ = "user"

    id = Column(Integer, primary_key=True)
    username = Column(String(), nullable=False, unique=True)
    first_name = Column(String(), nullable=False)
    last_name = Column(String(), nullable=False)
    password = Column(String(), nullable=False)
    password_expiry = Column(DateTime, nullable=False)


class UserSession(Base):
    """Represents a user session"""
    __tablename__ = "usersession"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("user.id"))
    user = relationship("User")
    token = Column(String(), nullable=False, unique=True)
    issued = Column(DateTime, default=datetime.datetime.now, nullable=False)
    lastactivity = Column(DateTime, default=datetime.datetime.now, nullable=False)
    expired = Column(DateTime)

