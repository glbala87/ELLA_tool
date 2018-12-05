import datetime
import pytz
from sqlalchemy import Column, Integer, Boolean, String, DateTime

from vardb.datamodel import Base


class Broadcast(Base):
    """Broadcast message"""
    __tablename__ = "broadcast"

    id = Column(Integer, primary_key=True)
    date_created = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.datetime.now(pytz.utc))
    message = Column(String, nullable=False)
    active = Column(Boolean, nullable=False)
