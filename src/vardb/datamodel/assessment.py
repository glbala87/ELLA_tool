"""vardb datamodel Assessment class"""

import datetime
from collections import defaultdict

from sqlalchemy import Column, Sequence, Integer, String, DateTime, ForeignKey, Table
from sqlalchemy.orm import relationship, backref
from sqlalchemy.ext.mutable import MutableDict
from sqlalchemy.ext.associationproxy import association_proxy
from sqlalchemy.dialects.postgresql import HSTORE
from sqlalchemy.schema import Index, ForeignKeyConstraint

from vardb.datamodel import Base
from vardb.datamodel import gene, annotation


class Assessment(Base):
    """Represents an assessment of one or more alleles."""
    __tablename__ = "assessment"

    id = Column(Integer, Sequence("id_assessment_seq"), primary_key=True)
    classification = Column(String(5), nullable=False)
    comment = Column(String(200))
    interpreterName = Column("interpreter_name", String(50))  # A database user
    status = Column(Integer, nullable=False, default=0)  # Intended usage: 0 = non-curated 1 = curated
    dateLastUpdate = Column("date_last_update", DateTime)
    dateSuperceeded = Column("date_superceeded", DateTime)
    previousAssessment_id = Column(Integer, ForeignKey("assessment.id"))
    previousAssessment = relationship("Assessment", uselist=False)
    allele_id = Column(Integer, ForeignKey("allele.id"))
    genepanelName = Column(String)
    genepanelVersion = Column(String)
    genepanel = relationship("Genepanel", uselist=False)
    transcript_id = Column(Integer, ForeignKey("transcript.id"))
    transcript = relationship("Transcript")
    annotation_id = Column(Integer, ForeignKey("annotation.id"))
    annotation = relationship("Annotation")
    weightedAnnotations = Column(MutableDict.as_mutable(HSTORE))
    # association-proxy 'references' can conceal usage of AssessmentReference association objects
    references = association_proxy("assessmentReference", "reference")

    __table_args__ = (ForeignKeyConstraint([genepanelName, genepanelVersion], ["genepanel.name", "genepanel.version"]),)

    def __repr__(self):
        return "<Assessment('%s','%s', '%s')>" % (self.classification, self.interpreterName, self.status)

    def __str__(self):
        return "%s, %s, %s" % (self.classification, self.status, self.dateLastUpdate)


class AssessmentReference(Base):
    """Association object between assessments and references.

    Note that Assessment uses an association proxy;
    usage of AssessmentReference can therefore be sidestepped
    if it is not necessary to change values to the extra attributes in this class.
    """
    __tablename__ = "assessment_reference"

    assessment_id = Column(Integer, ForeignKey("assessment.id"), primary_key=True)
    reference_id = Column(Integer, ForeignKey("reference.id"), primary_key=True)
    evaluation = Column(MutableDict.as_mutable(HSTORE))

    assessment = relationship(Assessment, backref=backref("assessmentReference", cascade="all, delete-orphan")) # TODO: Verify cascade
    reference = relationship("Reference")

    def __str__(self):
        return "%s, %s, %s" % (self.assessment, self.reference, self.evaluation)


class Reference(Base):
    """Represents a reference that brings information to this assessment."""
    __tablename__ = "reference"

    id = Column(Integer, Sequence("id_reference_seq"), primary_key=True)
    authors = Column(String(150))
    title = Column(String(400))
    journal = Column(String(200))
    year = Column(Integer)
    URL = Column(String(200))
    pubmedID = Column(Integer, unique=True)

    __table_args__ = (Index("ix_pubmedid", "pubmedID", unique=True), )

    def __repr__(self):
        return "<Reference('%s','%s', '%s')>" % (self.authors, self.title, self.year)

    def __str__(self):
        return "%s (%s) %s" % (self.authors, self.year, self.journal)

    def citation(self):
        return "%s (%s) %s %s" % (self.authors, self.year, self.title, self.journal)
