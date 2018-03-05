#!/usr/bin/env python

import datetime
import pytz
from sqlalchemy import Column, Integer, DateTime, Enum, String
from sqlalchemy import ForeignKey, ForeignKeyConstraint, UniqueConstraint
from sqlalchemy.orm import relationship, deferred
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.declarative import declared_attr

from vardb.datamodel.migration.ci_migration_base import Base
from vardb.util.mutjson import JSONMutableDict


class InterpretationMixin(object):

    id = Column(Integer, primary_key=True)
    genepanel_name = Column(String, nullable=False)
    genepanel_version = Column(String, nullable=False)

    user_state = Column("user_state", JSONMutableDict.as_mutable(JSONB), default={})
    state = Column(JSONMutableDict.as_mutable(JSONB), default={})
    status = Column(Enum("Not started", "Ongoing", "Done", name="interpretation_status"),
                    default="Not started", nullable=False)
    end_action = Column(Enum("Mark review", "Finalize", name="interpretation_endaction"))
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
    filtered = Column(Enum("FREQUENCY", "INTRON", "GENE", "UTR", name="interpretationsnapshot_filtered"),)  # If the allele was filtered, this describes which type of filtering

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

    def __repr__(self):
        return "<Interpretation('{}', '{}')>".format(str(self.analysis_id), self.status)


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

    def __repr__(self):
        return "<AlleleInterpretation('{}', '{}')>".format(str(self.allele_id), self.status)


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
