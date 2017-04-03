import datetime
from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Boolean


from vardb.datamodel import Base


class User(Base):
    """Represents a user."""
    __tablename__ = "user"

    id = Column(Integer, primary_key=True)
    username = Column(String(), nullable=False, unique=True)
    first_name = Column(String(), nullable=False)
    last_name = Column(String(), nullable=False)
    password = Column(String(), nullable=False)
    password_salt = Column(String(), nullable=False)
    password_expiry = Column(DateTime, nullable=False)


class Session(Base):
    """Represents a user session"""
    __tablename__ = "session"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("user.id"))
    token = Column(String(), nullable=False, unique=True)
    valid = Column(Boolean, default=True, nullable=False)
    issuedate = Column(DateTime, default=datetime.datetime.now, nullable=False)
    logoutdate = Column(DateTime)
