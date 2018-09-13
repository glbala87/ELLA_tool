#!/usr/bin/env python

import datetime
import pytz
from sqlalchemy import Column, Integer, DateTime, Enum, String, Boolean
from sqlalchemy import ForeignKey, ForeignKeyConstraint, UniqueConstraint, Index
from sqlalchemy.orm import relationship, deferred
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.declarative import declared_attr

from vardb.datamodel import Base
from vardb.util.mutjson import JSONMutableDict


class InterpretationMixin(object):

    id = Column(Integer, primary_key=True)
    genepanel_name = Column(String, nullable=False)
    genepanel_version = Column(String, nullable=False)
    user_state = Column(JSONMutableDict.as_mutable(JSONB), default={})
    state = Column(JSONMutableDict.as_mutable(JSONB), default={})
    status = Column(Enum("Not started", "Ongoing", "Done", name="interpretation_status"),
                    default="Not started", nullable=False)
    finalized = Column(Boolean)
    date_last_update = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.datetime.now(pytz.utc))
    date_created = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.datetime.now(pytz.utc))




    @declared_attr
    def user_id(cls):
        return Column(Integer, ForeignKey("user.id"))

    @declared_attr
    def user(cls):
        return relationship("User")

    @declared_attr
    def genepanel(cls):
        return relationship("Genepanel", uselist=False)

    @declared_attr
    def __table_args__(cls):
        return (ForeignKeyConstraint(['genepanel_name', 'genepanel_version'], ["genepanel.name", "genepanel.version"]),)

    @classmethod
    def create_next(cls, old):
        next_obj = cls()
        for attr in cls.__next_attrs__:
            setattr(next_obj, attr, getattr(old, attr))
        return next_obj


class InterpretationSnapshotMixin(object):

    id = Column(Integer, primary_key=True)
    date_created = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.datetime.now(pytz.utc))
    filtered = Column(Enum("FREQUENCY", "REGION", "GENE", "QUALITY", "SEGREGATION",  name="interpretationsnapshot_filtered"),)  # If the allele was filtered, this describes which type of filtering

    @declared_attr
    def annotation_id(cls):
        return Column(Integer, ForeignKey("annotation.id"), nullable=True)  # None for an excluded allele

    @declared_attr
    def customannotation_id(cls):
        return Column(Integer, ForeignKey("customannotation.id"))

    @declared_attr
    def alleleassessment_id(cls):
        return Column(Integer, ForeignKey("alleleassessment.id"))

    @declared_attr
    def presented_alleleassessment_id(cls):
        return Column(Integer, ForeignKey("alleleassessment.id"))

    @declared_attr
    def allelereport_id(cls):
        return Column(Integer, ForeignKey("allelereport.id"))

    @declared_attr
    def presented_allelereport_id(cls):
        return Column(Integer, ForeignKey("allelereport.id"))


class AnalysisInterpretation(Base, InterpretationMixin):
    """Represents an Interpretation by a labengineer

    This corresponds to one interpretation 'round' of an analysis.
    The table stores both normal state and user-specific state for each round,
    while keeping a history of the state upon update.
    """
    __tablename__ = "analysisinterpretation"

    __next_attrs__ = ['analysis_id', 'state', 'genepanel_name', 'genepanel_version']

    analysis_id = Column(Integer, ForeignKey("analysis.id"), nullable=False)
    analysis = relationship("Analysis", uselist=False)
    workflow_status = Column(Enum("Not ready", "Interpretation", "Review", "Medical review",
                             name="analysisinterpretation_workflow_status"), default="Interpretation", nullable=False)

    def __repr__(self):
        return "<Interpretation('{}', '{}')>".format(str(self.analysis_id), self.status)

Index(
    'ix_analysisinterpretation_analysisid_ongoing_unique',
    AnalysisInterpretation.analysis_id,
    postgresql_where=(AnalysisInterpretation.status.in_(['Ongoing', 'Not started'])),
    unique=True
)


class AnalysisInterpretationSnapshot(Base, InterpretationSnapshotMixin):
    """
    Represents a snapshot of a allele interpretation,
    at the time when it was marked as 'Done'.
    It's logging all relevant context for the interpretation.
    """
    __tablename__ = "analysisinterpretationsnapshot"

    analysisinterpretation_id = Column(Integer, ForeignKey("analysisinterpretation.id"), nullable=False,)
    analysisinterpretation = relationship("AnalysisInterpretation", backref='snapshots')
    allele_id = Column(Integer, ForeignKey("allele.id"), nullable=False)
    __table_args__ = (UniqueConstraint("analysisinterpretation_id", "allele_id"), )


class AlleleInterpretation(Base, InterpretationMixin):
    """Represents an interpretation of an allele by a labengineer

    This corresponds to one interpretation 'round' of an allele.
    The table stores both normal state and user-specific state for each round,
    while keeping a history of the state upon update.
    """
    __tablename__ = "alleleinterpretation"

    __next_attrs__ = ['allele_id', 'state', 'genepanel_name', 'genepanel_version']

    allele_id = Column(Integer, ForeignKey("allele.id"), nullable=False)
    allele = relationship("Allele", uselist=False)
    workflow_status = Column(Enum("Interpretation", "Review",
                             name="alleleinterpretation_workflow_status"), default="Interpretation", nullable=False)

    def __repr__(self):
        return "<AlleleInterpretation('{}', '{}')>".format(str(self.allele_id), self.status)

Index(
    'ix_alleleinterpretation_alleleid_ongoing_unique',
    AlleleInterpretation.allele_id,
    postgresql_where=(AlleleInterpretation.status.in_(['Ongoing', 'Not started'])),
    unique=True
)


class AlleleInterpretationSnapshot(Base, InterpretationSnapshotMixin):
    """
    Represents a snapshot of a allele interpretation,
    at the time when it was marked as 'Done'.
    It's logging all relevant context for the interpretation.
    """
    __tablename__ = "alleleinterpretationsnapshot"

    alleleinterpretation_id = Column(Integer, ForeignKey("alleleinterpretation.id"), nullable=False)
    alleleinterpretation = relationship("AlleleInterpretation", backref='snapshots')
    allele_id = Column(Integer, ForeignKey("allele.id"), nullable=False)
    __table_args__ = (UniqueConstraint("alleleinterpretation_id", "allele_id"), )


class InterpretationStateHistory(Base):
    """
    Holds the history of the state for the interpretations.
    Every time the [allele|analysis]interpretation state is updated (i.e. when user saves),
    it's copied into this table.
    """
    __tablename__ = "interpretationstatehistory"

    id = Column(Integer, primary_key=True)
    alleleinterpretation_id = Column(Integer, ForeignKey("alleleinterpretation.id"))
    analysisinterpretation_id = Column(Integer, ForeignKey("analysisinterpretation.id"))
    user_id = Column(Integer, ForeignKey("user.id"), nullable=False)
    date_created = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.datetime.now(pytz.utc))
    state = Column(JSONMutableDict.as_mutable(JSONB), nullable=False)
