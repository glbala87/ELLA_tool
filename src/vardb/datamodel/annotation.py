"""varDB datamodel Annotation class"""
import datetime

from sqlalchemy import Column, Sequence, Integer, String, DateTime
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.mutable import MutableDict
from sqlalchemy import ForeignKey
from sqlalchemy.orm import relationship

from vardb.datamodel import Base


class Annotation(Base):
    """Represents a set of annotations for an allele"""
    __tablename__ = "annotation"

    id = Column(Integer, Sequence("id_annotation_seq"), primary_key=True)
    annotations = Column(JSONB)
    previousAnnotation_id = Column("previous_annotation_id", Integer,
                                   ForeignKey("annotation.id"))
    # use remote_side to store foreignkey for previousAnnotation in 'this' parent:
    previousAnnotation = relationship("Annotation", uselist=False, remote_side=id)
    dateSuperceeded = Column("date_superceeded", DateTime)

    def __repr__(self):
        return "<Annotation('%s', '%s', '%s')>" % (self.annotations,
                                                   self.previousAnnotation,
                                                   self.dateSuperceeded)
