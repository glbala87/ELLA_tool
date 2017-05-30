import datetime

from sqlalchemy import Column, Enum, Integer, String, DateTime, ForeignKey, Table, BigInteger
from sqlalchemy.orm import relationship
from sqlalchemy.schema import Index, ForeignKeyConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy_utils.types import TSVectorType
from sqlalchemy_searchable import SearchQueryMixin

from vardb.datamodel import Base
from vardb.datamodel import gene, annotation, user, sample  # Needed, implicit imports used by sqlalchemy
from vardb.util.mutjson import JSONMutableDict


class Attachment(Base):
    __tablename__ = "attachment"

    id = Column(Integer, primary_key=True)
    sha256 = Column(String(), unique=True)
    filename = Column(String(), nullable=False)
    size = Column(BigInteger)
    date_created = Column(DateTime, default=datetime.datetime.now)
    mimetype = Column(String())
    extension = Column(String())


class AlleleAssessmentAttachment(Base):
    __tablename__ = "alleleassessmentattachment"

    id = Column(Integer, primary_key=True)
    alleleassessment_id = Column(Integer, ForeignKey("alleleassessment.id"), nullable=False)
    alleleassessment = relationship("AlleleAssessment")
    attachment_id = Column(Integer, ForeignKey("attachment.id"), nullable=False)
    attachment = relationship("Attachment")


# class ReferenceAttachment(Base):
#     __tablename__ = "referenceattachment"
#
#     id = Column(Integer, primary_key=True)
#     reference_id = Column(Integer, ForeignKey("reference.id"), nullable=False, unique=True)
#     attachment_id = Column(Integer, ForeignKey("attachment.id"), nullable=False)
#     attachment = relationship("Attachment")

