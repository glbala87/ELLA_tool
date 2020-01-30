import datetime
import pytz
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import INET

from vardb.datamodel import Base


class ResourceLog(Base):
    """Logs HTTP resource access"""

    __tablename__ = "resourcelog"

    id = Column(Integer, primary_key=True)
    remote_addr = Column(INET, nullable=False)
    time = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.datetime.now(pytz.utc),
        index=True,
    )
    duration = Column(Integer, nullable=False)
    usersession_id = Column(Integer, ForeignKey("usersession.id"))
    method = Column(String, nullable=False)
    resource = Column(String, nullable=False)
    query = Column(String, nullable=False)
    response = Column(String)
    response_size = Column(Integer, nullable=False)
    payload = Column(String)
    payload_size = Column(Integer, nullable=False)
    statuscode = Column(Integer, nullable=False)


class CliLog(Base):
    """Logs CLI actions"""

    __tablename__ = "clilog"

    id = Column(Integer, primary_key=True)
    time = Column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.datetime.now(pytz.utc)
    )
    user = Column(String, nullable=False)
    group = Column(String, nullable=False)
    groupcommand = Column(String, nullable=False)
    command = Column(String, nullable=False)
    reason = Column(String)
    output = Column(String, nullable=False)
