import datetime
import pytz
from sqlalchemy import Column, Integer, String, DateTime, BigInteger
from vardb.datamodel import Base


class Attachment(Base):
    __tablename__ = "attachment"

    id = Column(Integer, primary_key=True)
    sha256 = Column(String())
    filename = Column(String(), nullable=False)
    size = Column(BigInteger)
    date_created = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.datetime.now(pytz.utc))
    mimetype = Column(String())
    extension = Column(String())

