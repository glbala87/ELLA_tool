"""varDB datamodel Annotation class"""
import datetime
from sqlalchemy import Column, Sequence, Integer, DateTime
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy import ForeignKey
from sqlalchemy.orm import relationship

from vardb.util.mutjson import JSONMutableDict

from . import Base


class Annotation(Base):
    """Represents a set of annotations for an allele"""
    __tablename__ = "annotation"

    id = Column(Integer, Sequence("id_annotation_seq"), primary_key=True)
    allele_id = Column(Integer, ForeignKey("allele.id"))
    allele = relationship("Allele", uselist=False)
    annotations = Column(JSONMutableDict.as_mutable(JSONB))
    previousAnnotation_id = Column("previous_annotation_id", Integer,
                                   ForeignKey("annotation.id"))
    # use remote_side to store foreignkey for previousAnnotation in 'this' parent:
    previousAnnotation = relationship("Annotation", uselist=False, remote_side=id)
    dateSuperceeded = Column("date_superceeded", DateTime)

    def __repr__(self):
        return "<Annotation('%s', '%s', '%s')>" % (self.annotations,
                                                   self.previousAnnotation,
                                                   self.dateSuperceeded)


class CustomAnnotation(Base):
    """Represents a set of annotations for an allele, created by a user"""
    __tablename__ = "customannotation"

    id = Column(Integer, Sequence("id_customannotation_seq"), primary_key=True)
    annotations = Column(JSONMutableDict.as_mutable(JSONB))
    allele_id = Column(Integer, ForeignKey("allele.id"))
    allele = relationship("Allele", uselist=False)
    user_id = Column(Integer, ForeignKey("user.id"))
    user = relationship("User", uselist=False)
    previousAnnotation_id = Column("previous_annotation_id", Integer,
                                   ForeignKey("customannotation.id"))
    # use remote_side to store foreignkey for previousAnnotation in 'this' parent:
    previousAnnotation = relationship("CustomAnnotation", uselist=False, remote_side=id)
    dateSuperceeded = Column("date_superceeded", DateTime)
    dateLastUpdate = Column("date_last_update", DateTime, nullable=False, default=datetime.datetime.now)

    def __repr__(self):
        return "<CustomAnnotation('%s')>" % (self.annotations)
