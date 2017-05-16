import datetime
from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Boolean, Table
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.schema import ForeignKeyConstraint

from vardb.datamodel import Base
from vardb.util.mutjson import JSONMutableDict

# UserUserGroup = Table('userusergroup', Base.metadata,
#     Column('user_id', Integer, ForeignKey('user.id')),
#     Column('usergroup_id', Integer, ForeignKey('usergroup.id'))
# )


# Links user groups to genepanels
UserGroupGenepanel = Table('usergroupgenepanel', Base.metadata,
    Column('usergroup_id', Integer, ForeignKey('usergroup.id')),
    Column('genepanel_name', String, nullable=False),
    Column('genepanel_version', String, nullable=False),
    ForeignKeyConstraint(['genepanel_name', 'genepanel_version'], ['genepanel.name', 'genepanel.version'], ondelete="CASCADE")
)


class User(Base):
    """Represents a user."""
    __tablename__ = "user"

    id = Column(Integer, primary_key=True)
    username = Column(String(), nullable=False, unique=True)
    first_name = Column(String(), nullable=False)
    last_name = Column(String(), nullable=False)
    group_id = Column(Integer, ForeignKey("usergroup.id"), nullable=False)
    password = Column(String(), nullable=False)
    password_expiry = Column(DateTime, nullable=False)
    active = Column(Boolean, default=True, nullable=False)
    incorrect_logins = Column(Integer, default=0, nullable=False)


class UserGroup(Base):
    __tablename__ = "usergroup"

    id = Column(Integer, primary_key=True)
    name = Column(String(), nullable=False, unique=True)
    genepanels = relationship('Genepanel', secondary=UserGroupGenepanel)


class UserSession(Base):
    """Represents a user session"""
    __tablename__ = "usersession"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("user.id"))
    user = relationship("User")
    token = Column(String(), nullable=False, unique=True)
    issued = Column(DateTime, default=datetime.datetime.now, nullable=False)
    lastactivity = Column(DateTime, default=datetime.datetime.now, nullable=False)
    expires = Column(DateTime, nullable=False)
    expired = Column(DateTime)


class UserOldPassword(Base):
    __tablename__ = "useroldpassword"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("user.id"))
    password = Column(String(), nullable=False)
    expired = Column(DateTime, default=datetime.datetime.now, nullable=False)
