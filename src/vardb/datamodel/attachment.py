import datetime
from sqlalchemy import Column, Integer, String, DateTime, BigInteger
from vardb.datamodel import Base


class Attachment(Base):
    __tablename__ = "attachment"

    id = Column(Integer, primary_key=True)
    sha256 = Column(String(), unique=True)
    filename = Column(String(), nullable=False)
    size = Column(BigInteger)
    date_created = Column(DateTime, default=datetime.datetime.now)
    mimetype = Column(String())
    extension = Column(String())

