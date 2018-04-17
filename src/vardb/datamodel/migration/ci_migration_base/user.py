import datetime
import pytz
from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Boolean, Table
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.schema import ForeignKeyConstraint

from vardb.datamodel.migration.ci_migration_base import Base
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
    ForeignKeyConstraint(['genepanel_name', 'genepanel_version'], ['genepanel.name', 'genepanel.version'])
)


class User(Base):
    """Represents a user."""
    __tablename__ = "user"

    id = Column(Integer, primary_key=True)
    username = Column(String(), nullable=False, unique=True)
    first_name = Column(String(), nullable=False)
    last_name = Column(String(), nullable=False)
    group_id = Column(Integer, ForeignKey("usergroup.id"), nullable=False)
    group = relationship("UserGroup", uselist=False, backref="users")
    password = Column(String(), nullable=False)
    password_expiry = Column(DateTime(timezone=True), nullable=False)
    active = Column(Boolean, default=True, nullable=False)
    incorrect_logins = Column(Integer, default=0, nullable=False)
    config = Column(JSONMutableDict.as_mutable(JSONB), default={})


class UserGroup(Base):
    __tablename__ = "usergroup"

    id = Column(Integer, primary_key=True)
    name = Column(String(), nullable=False, unique=True)
    genepanels = relationship('Genepanel', secondary=UserGroupGenepanel)
    config = Column(JSONMutableDict.as_mutable(JSONB), default={})
    default_import_genepanel_name = Column(String)
    default_import_genepanel_version = Column(String)
    default_import_genepanel = relationship("Genepanel", uselist=False)

    __table_args__ = (ForeignKeyConstraint([default_import_genepanel_name, default_import_genepanel_version], ["genepanel.name", "genepanel.version"]),)


class UserSession(Base):
    """Represents a user session"""
    __tablename__ = "usersession"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("user.id"))
    user = relationship("User")
    token = Column(String(), nullable=False, unique=True)
    issued = Column(DateTime(timezone=True), default=lambda: datetime.datetime.now(pytz.utc), nullable=False)
    lastactivity = Column(DateTime(timezone=True), default=lambda: datetime.datetime.now(pytz.utc), nullable=False)
    expires = Column(DateTime(timezone=True), nullable=False)
    logged_out = Column(DateTime(timezone=True))


class UserOldPassword(Base):
    __tablename__ = "useroldpassword"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("user.id"))
    password = Column(String(), nullable=False)
    expired = Column(DateTime(timezone=True), default=lambda: datetime.datetime.now(pytz.utc), nullable=False)
