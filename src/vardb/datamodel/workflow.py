#!/usr/bin/env python

import datetime

from sqlalchemy import Column, Sequence, Integer, DateTime, Enum, String
from sqlalchemy import ForeignKey, ForeignKeyConstraint
from sqlalchemy.orm import relationship, deferred
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.declarative import declared_attr

from vardb.datamodel import Base
from vardb.util.mutjson import JSONMutableDict


class InterpretationMixin(object):
    genepanel_name = Column(String, nullable=False)
    genepanel_version = Column(String, nullable=False)

    user_state = Column("user_state", JSONMutableDict.as_mutable(JSONB), default={})
    state = Column(JSONMutableDict.as_mutable(JSONB), default={})
    status = Column(Enum("Not started", "Ongoing", "Done", name="interpretation_status"),
                    default="Not started", nullable=False)
    date_last_update = Column(DateTime, nullable=False, default=datetime.datetime.now)

    @declared_attr
    def state_history(cls):
        return deferred(Column(JSONMutableDict.as_mutable(JSONB), default={}))

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

    filtered = Column(Enum("CLASS1", "INTRON", "GENE", name="interpretationsnapshot_filtered"),)  # If the allele was filtered, this describes which type of filtering

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

    id = Column(Integer, Sequence("id_analysisinterpretation_seq"), primary_key=True)
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

    id = Column(Integer, Sequence("id_analysisinterpretationsnapshot_seq"), primary_key=True)
    analysisinterpretation_id = Column(Integer, ForeignKey("analysisinterpretation.id"), nullable=False,)
    analysisinterpretation = relationship("AnalysisInterpretation", backref='snapshots')
    allele_id = Column(Integer, ForeignKey("allele.id"), nullable=False)


class AlleleInterpretation(Base, InterpretationMixin):
    """Represents an interpretation of an allele by a labengineer

    This corresponds to one interpretation 'round' of an allele.
    The table stores both normal state and user-specific state for each round,
    while keeping a history of the state upon update.
    """
    __tablename__ = "alleleinterpretation"

    __next_attrs__ = ['allele_id', 'state', 'genepanel_name', 'genepanel_version']

    id = Column(Integer, Sequence("id_alleleinterpretation_seq"), primary_key=True)
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

    id = Column(Integer, Sequence("id_alleleinterpretationsnapshot_seq"), primary_key=True)
    alleleinterpretation_id = Column(Integer, ForeignKey("alleleinterpretation.id"), nullable=False)
    alleleinterpretation = relationship("AlleleInterpretation", backref='snapshots')
    allele_id = Column(Integer, ForeignKey("allele.id"), nullable=False)
