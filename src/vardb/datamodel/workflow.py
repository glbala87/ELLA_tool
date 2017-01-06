#!/usr/bin/env python
"""varDB datamodel classes for entities that relate to samples."""

import datetime

from sqlalchemy import Column, Sequence, Integer, DateTime, Enum, String
from sqlalchemy import ForeignKey, ForeignKeyConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import JSONB

from vardb.datamodel import Base
from vardb.util.mutjson import JSONMutableDict


class AnalysisInterpretation(Base):
    """Represents an Interpretation by a labengineer

    This corresponds to one interpretation 'round' of an analysis.
    The table stores both normal state and user-specific state for each round,
    while keeping a history of the state upon update.

    :note: The stateHistory column can potentially be heavy in extreme cases,
    so you can defer loading it when you don't need it.
    (TODO: defer by default?)
    """
    __tablename__ = "analysisinterpretation"

    __next_attrs__ = ['analysis_id', 'state', 'genepanel_name', 'genepanel_version']

    id = Column(Integer, Sequence("id_analysisinterpretation_seq"), primary_key=True)
    analysis_id = Column(Integer, ForeignKey("analysis.id"), nullable=False)
    analysis = relationship("Analysis", uselist=False)
    genepanel_name = Column(String)
    genepanel_version = Column(String)
    genepanel = relationship("Genepanel", uselist=False)

    user_state = Column("user_state", JSONMutableDict.as_mutable(JSONB), default={})
    user_id = Column(Integer, ForeignKey("user.id"))
    user = relationship("User", uselist=False, backref='analysisinterpretations')
    state = Column(JSONMutableDict.as_mutable(JSONB), default={})
    state_history = Column(JSONMutableDict.as_mutable(JSONB), default={})
    status = Column(Enum("Not started", "Ongoing", "Done", name="interpretation_status"),
                    default="Not started", nullable=False)
    date_last_update = Column(DateTime, nullable=False, default=datetime.datetime.now)
    __table_args__ = (ForeignKeyConstraint([genepanel_name, genepanel_version], ["genepanel.name", "genepanel.version"]),)

    def __repr__(self):
        return "<Interpretation('{}', '{}')>".format(str(self.analysis_id), self.status)

    @classmethod
    def create_next(cls, old):
        next_obj = cls()
        for attr in cls.__next_attrs__:
            setattr(next_obj, attr, getattr(old, attr))
        return next_obj


class AnalysisInterpretationSnapshot(Base):
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

    genepanel_name = Column(String)
    genepanel_version = Column(String)
    genepanel = relationship("Genepanel", uselist=False)

    annotation_id = Column(Integer, ForeignKey("annotation.id"), nullable=True)  # None for an excluded allele
    customannotation_id = Column(Integer, ForeignKey("customannotation.id"))

    alleleassessment_id = Column(Integer, ForeignKey("alleleassessment.id"))
    presented_alleleassessment_id = Column(Integer, ForeignKey("alleleassessment.id"))

    allelereport_id = Column(Integer, ForeignKey("allelereport.id"))
    presented_allelereport_id = Column(Integer, ForeignKey("allelereport.id"))

    filtered = Column(Enum("CLASS1", "INTRON", "GENE", name="analysisinterpretationsnaptshot_filtered"),)  # If the allele was filtered, this describes which type of filtering

    alleleassessment = relationship("AlleleAssessment", foreign_keys=alleleassessment_id)
    presented_alleleassessment = relationship("AlleleAssessment", foreign_keys=presented_alleleassessment_id)

    __table_args__ = (ForeignKeyConstraint([genepanel_name, genepanel_version], ["genepanel.name", "genepanel.version"]),)


class AlleleInterpretation(Base):
    """Represents an interpretation of an allele by a labengineer

    This corresponds to one interpretation 'round' of an allele.
    The table stores both normal state and user-specific state for each round,
    while keeping a history of the state upon update.

    :note: The stateHistory column can potentially be heavy in extreme cases,
    so you can defer loading it when you don't need it.
    (TODO: defer by default?)
    """
    __tablename__ = "alleleinterpretation"

    __next_attrs__ = ['allele_id', 'state', 'genepanel_name', 'genepanel_version']

    id = Column(Integer, Sequence("id_alleleinterpretation_seq"), primary_key=True)
    allele_id = Column(Integer, ForeignKey("allele.id"), nullable=False)
    allele = relationship("Allele", uselist=False)
    genepanel_name = Column(String)
    genepanel_version = Column(String)
    genepanel = relationship("Genepanel", uselist=False)
    user_state = Column("user_state", JSONMutableDict.as_mutable(JSONB), default={})
    user_id = Column(Integer, ForeignKey("user.id"))
    user = relationship("User", uselist=False)
    state = Column(JSONMutableDict.as_mutable(JSONB), default={})
    state_history = Column(JSONMutableDict.as_mutable(JSONB), default={})
    status = Column(Enum("Not started", "Ongoing", "Done", name="interpretation_status"),
                    default="Not started", nullable=False)
    date_last_update = Column(DateTime, nullable=False, default=datetime.datetime.now)
    __table_args__ = (ForeignKeyConstraint([genepanel_name, genepanel_version], ["genepanel.name", "genepanel.version"]),)

    def __repr__(self):
        return "<AlleleInterpretation('{}', '{}')>".format(str(self.allele_id), self.status)

    @classmethod
    def create_next(cls, old):
        next_obj = cls()
        for attr in cls.__next_attrs__:
            setattr(next_obj, attr, getattr(old, attr))
        return next_obj


class AlleleInterpretationSnapshot(Base):
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
    annotation_id = Column(Integer, ForeignKey("annotation.id"), nullable=True)  # None for an excluded allele
    customannotation_id = Column(Integer, ForeignKey("customannotation.id"))

    alleleassessment_id = Column(Integer, ForeignKey("alleleassessment.id"))
    presented_alleleassessment_id = Column(Integer, ForeignKey("alleleassessment.id"))

    allelereport_id = Column(Integer, ForeignKey("allelereport.id"))
    presented_allelereport_id = Column(Integer, ForeignKey("allelereport.id"))

    alleleassessment = relationship("AlleleAssessment", foreign_keys=alleleassessment_id)
    presented_alleleassessment = relationship("AlleleAssessment", foreign_keys=presented_alleleassessment_id)
