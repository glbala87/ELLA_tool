"""vardb datamodel Assessment class"""
import datetime
import pytz

from sqlalchemy import Column, Enum, Integer, String, DateTime, ForeignKey, Table
from sqlalchemy.orm import relationship
from sqlalchemy.schema import Index, ForeignKeyConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy_utils.types import TSVectorType
from sqlalchemy_searchable import SearchQueryMixin

from vardb.datamodel import Base
from vardb.datamodel import gene, annotation, user, sample, attachment  # Needed, implicit imports used by sqlalchemy
from vardb.util.mutjson import JSONMutableDict


AlleleAssessmentReferenceAssessment = Table('alleleassessmentreferenceassessment', Base.metadata,
    Column('alleleassessment_id', Integer, ForeignKey('alleleassessment.id')),
    Column('referenceassessment_id', Integer, ForeignKey('referenceassessment.id'))
)

AlleleAssessmentAttachment = Table('alleleassessmentattachment', Base.metadata,
    Column('alleleassessment_id', Integer, ForeignKey('alleleassessment.id')),
    Column('attachment_id', Integer, ForeignKey('attachment.id')),
)

class AlleleAssessment(Base):
    """Represents an assessment of one allele."""
    __tablename__ = "alleleassessment"

    id = Column(Integer, primary_key=True)
    classification = Column(Enum('1', '2', '3', '4', '5', 'T', native_enum=False), nullable=False)
    evaluation = Column(JSONMutableDict.as_mutable(JSONB), default={})
    user_id = Column(Integer, ForeignKey("user.id"))
    user = relationship("User", uselist=False)
    date_created = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.datetime.now(pytz.utc))
    date_superceeded = Column(DateTime(timezone=True))
    previous_assessment_id = Column(Integer, ForeignKey("alleleassessment.id"))
    previous_assessment = relationship("AlleleAssessment", uselist=False)
    allele_id = Column(Integer, ForeignKey("allele.id"), nullable=False)
    allele = relationship("Allele", uselist=False, backref='assessments')
    genepanel_name = Column(String, nullable=False)
    genepanel_version = Column(String, nullable=False)
    genepanel = relationship("Genepanel", uselist=False)
    analysis_id = Column(Integer, ForeignKey("analysis.id"))
    annotation_id = Column(Integer, ForeignKey("annotation.id"))
    annotation = relationship("Annotation")
    custom_annotation_id = Column(Integer, ForeignKey("customannotation.id"))
    custom_annotation = relationship("CustomAnnotation")


    referenceassessments = relationship("ReferenceAssessment",
                                        secondary=AlleleAssessmentReferenceAssessment)
    attachments = relationship("Attachment", secondary=AlleleAssessmentAttachment)

    __table_args__ = (ForeignKeyConstraint([genepanel_name, genepanel_version], ["genepanel.name", "genepanel.version"]),)

    def __repr__(self):
        return "<AlleleAssessment('%s','%s', '%s')>" % (self.id, self.classification, str(self.user))

    def __str__(self):
        return "%s, %s" % (self.classification, self.date_last_update)


class ReferenceAssessment(Base):
    """Association object between assessments and references.

    Note that Assessment uses an association proxy;
    usage of AssessmentReference can therefore be sidestepped
    if it is not necessary to change values to the extra attributes in this class.
    """
    __tablename__ = "referenceassessment"

    id = Column(Integer, primary_key=True)
    reference_id = Column(Integer, ForeignKey("reference.id"), nullable=False)
    reference = relationship("Reference")
    evaluation = Column(JSONMutableDict.as_mutable(JSONB), default={})
    user_id = Column(Integer, ForeignKey("user.id"))
    user = relationship("User", uselist=False)
    date_created = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.datetime.now(pytz.utc))
    date_superceeded = Column(DateTime(timezone=True))
    genepanel_name = Column(String, nullable=False)
    genepanel_version = Column(String, nullable=False)
    genepanel = relationship("Genepanel", uselist=False)
    allele_id = Column(Integer, ForeignKey("allele.id"), nullable=False)
    allele = relationship("Allele", uselist=False)
    previous_assessment_id = Column(Integer, ForeignKey("referenceassessment.id"))
    previous_assessment = relationship("ReferenceAssessment", uselist=False)
    analysis_id = Column(Integer, ForeignKey("analysis.id"))
    __table_args__ = (ForeignKeyConstraint([genepanel_name, genepanel_version], ["genepanel.name", "genepanel.version"]),)

    def __str__(self):
        return "%s, %s, %s" % (str(self.user), self.reference, self.evaluation)


class Reference(Base, SearchQueryMixin):
    """Represents a reference that brings information to this assessment."""
    __tablename__ = "reference"

    id = Column(Integer, primary_key=True)
    authors = Column(String())
    title = Column(String())
    journal = Column(String())
    abstract = Column(String())
    year = Column(String())
    pubmed_id = Column(Integer, unique=True)

    search = Column(TSVectorType("authors", "title", "journal", "year",
                    weights={"authors": 'A', "title": 'A', "journal": 'B', "year": 'C'}))

    __table_args__ = (Index("ix_pubmedid", "pubmed_id", unique=True), )

    def __repr__(self):
        return "<Reference('%s','%s', '%s')>" % (self.authors, self.title, self.year)

    def __str__(self):
        return "%s (%s) %s" % (self.authors, self.year, self.journal)

    def citation(self):
        return "%s (%s) %s %s" % (self.authors, self.year, self.title, self.journal)


class AlleleReport(Base):
    """Represents a report for one allele. The report is aimed at the
       clinicians as compared to alleleassessment which is aimed at fellow
       interpreters. The report might not change as often as the alleleassessment."""

    __tablename__ = "allelereport"

    id = Column(Integer, primary_key=True)
    evaluation = Column(JSONMutableDict.as_mutable(JSONB), default={})
    user_id = Column(Integer, ForeignKey("user.id"))
    user = relationship("User", uselist=False)
    date_created = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.datetime.now(pytz.utc))
    date_superceeded = Column(DateTime(timezone=True))
    previous_report_id = Column(Integer, ForeignKey("allelereport.id"))
    previous_report = relationship("AlleleReport", uselist=False)
    allele_id = Column(Integer, ForeignKey("allele.id"), nullable=False)
    allele = relationship("Allele", uselist=False, backref='reports')
    analysis_id = Column(Integer, ForeignKey("analysis.id"))
    alleleassessment_id = Column(Integer, ForeignKey("alleleassessment.id"))
    alleleassessment = relationship("AlleleAssessment")

    def __repr__(self):
        return "<AlleleReport('%s','%s', '%s')>" % (self.id, self.allele_id, str(self.user))
