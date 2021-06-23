"""varDB datamodel Annotation class"""
import datetime
import pytz
from sqlalchemy import Column, Integer, DateTime, Index, FetchedValue
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy import ForeignKey
from sqlalchemy.orm import relationship

from vardb.util.mutjson import JSONMutableDict, JSONMutableList
from vardb.datamodel import Base


class Annotation(Base):
    """Represents a set of annotations for an allele"""

    __tablename__ = "annotation"

    id = Column(Integer, primary_key=True)
    allele_id = Column(Integer, ForeignKey("allele.id"), index=True)
    allele = relationship("Allele", uselist=False)
    annotations = Column(JSONMutableDict.as_mutable(JSONB))
    schema_version = Column(Integer, nullable=False, server_default=FetchedValue())
    previous_annotation_id = Column(Integer, ForeignKey("annotation.id"))
    # use remote_side to store foreignkey for previous_annotation in 'this' parent:
    previous_annotation = relationship("Annotation", uselist=False, remote_side=id)
    date_superceeded = Column("date_superceeded", DateTime(timezone=True))
    date_created = Column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.datetime.now(pytz.utc)
    )
    annotation_config_id = Column(
        Integer, ForeignKey("annotationconfig.id"), index=True, nullable=False
    )
    genotype = relationship("AnnotationConfig", backref="annotations")

    def __repr__(self):
        return "<Annotation('%s', '%s', '%s')>" % (
            self.annotations,
            self.previous_annotation,
            self.date_superceeded,
        )


Index(
    "ix_annotation_unique",
    Annotation.allele_id,
    postgresql_where=(Annotation.date_superceeded.is_(None)),
    unique=True,
)


class CustomAnnotation(Base):
    """Represents a set of annotations for an allele, created by a user"""

    __tablename__ = "customannotation"

    id = Column(Integer, primary_key=True)
    annotations = Column(JSONMutableDict.as_mutable(JSONB))

    allele_id = Column(Integer, ForeignKey("allele.id"))
    allele = relationship("Allele", uselist=False)
    user_id = Column(Integer, ForeignKey("user.id"))
    user = relationship("User", uselist=False)
    previous_annotation_id = Column(
        "previous_annotation_id", Integer, ForeignKey("customannotation.id")
    )
    # use remote_side to store foreignkey for previous_annotation in 'this' parent:
    previous_annotation = relationship("CustomAnnotation", uselist=False, remote_side=id)
    date_superceeded = Column(DateTime(timezone=True))
    date_created = Column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.datetime.now(pytz.utc)
    )

    def __repr__(self):
        return "<CustomAnnotation('%s')>" % (self.annotations)


Index(
    "ix_customannotation_unique",
    CustomAnnotation.allele_id,
    postgresql_where=(CustomAnnotation.date_superceeded.is_(None)),
    unique=True,
)


class AnnotationConfig(Base):
    __tablename__ = "annotationconfig"
    id = Column(Integer, primary_key=True)
    deposit = Column(JSONMutableList.as_mutable(JSONB), nullable=False, default=lambda: {})
    view = Column(JSONMutableList.as_mutable(JSONB), nullable=False, default=lambda: {})
    date_created = Column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.datetime.now(pytz.utc)
    )
