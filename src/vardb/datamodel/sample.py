#!/usr/bin/env python
"""varDB datamodel classes for entities that relate to samples."""

import datetime

from sqlalchemy import Column, Sequence, Integer, String, DateTime, Enum
from sqlalchemy import ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.schema import Index, ForeignKeyConstraint
from sqlalchemy.dialects.postgresql import JSONB

from vardb.datamodel import Base
from vardb.util.mutjson import JSONMutableDict


class Sample(Base):
    """Represents a sample (aka one sequencing run of 1 biological sample)

    Can represent samples from two types of technologies, Sanger and HTS.

    Note: there can be multiple samples with same name in database, and they might differ in genotypes.
    This happens when multiple analyses, using the same sample data in pipeline, is imported.
    They can have been run on different regions.
    """
    __tablename__ = "sample"

    id = Column(Integer, Sequence("id_sample_seq"), primary_key=True)
    identifier = Column(String(), nullable=False)
    analysis_id = Column(Integer, ForeignKey("analysis.id"), nullable=False)
    analysis = relationship('Analysis', backref='samples')
    sample_type = Column(Enum("HTS", "Sanger", name="sample_type"), nullable=False)
    deposit_date = Column(DateTime, nullable=False, default=datetime.datetime.now)
    sample_config = Column(JSONMutableDict.as_mutable(JSONB))  # includes capturekit and more

    __table_args__ = (Index("ix_sampleidentifier", "identifier"), )

    def __repr__(self):
        return "<Sample('%s', '%s')>" % (self.identifier, self.sample_type)


class AnalysisFinalized(Base):
    """
    Represents a snapshot of a finalized analysis,
    logging all relevant information for every allele
    involved in the analysis, upon finalization.

    If an allele id is given two times for same analysis id,
    it was first served as part of the filtered data (class 1 or intron),
    and then included by the user as part of the interpretation,
    giving it an assessment.
    """
    __tablename__ = "analysisfinalized"

    id = Column(Integer, Sequence("id_analysisfinalized_seq"), primary_key=True)
    analysis_id = Column(Integer, ForeignKey("analysis.id"), nullable=False)
    allele_id = Column(Integer, ForeignKey("allele.id"), nullable=False)
    annotation_id = Column(Integer, ForeignKey("annotation.id"), nullable=False)
    customannotation_id = Column(Integer, ForeignKey("customannotation.id"))
    alleleassessment_id = Column(Integer, ForeignKey("alleleassessment.id"))
    allelereport_id = Column(Integer, ForeignKey("allelereport.id"))
    filtered = Column(Enum("CLASS1", "INTRON", name="analysis_filtered"),)  # If the allele was filtered, this describes which type of filtering


class Analysis(Base):
    """Represents a bioinformatical pipeline analysis

    An Analysis will have produced variant descriptions (e.g. VCF),
    that are an object for Interpretation.
    """
    __tablename__ = "analysis"

    id = Column(Integer, Sequence("id_analysis_seq"), primary_key=True)
    name = Column(String(), nullable=False, unique=True)
    genepanel_name = Column(String)
    genepanel_version = Column(String)
    genepanel = relationship("Genepanel", uselist=False)
    deposit_date = Column("deposit_date", DateTime, nullable=False, default=datetime.datetime.now)
    analysis_config = Column(JSONMutableDict.as_mutable(JSONB))
    interpretations = relationship("Interpretation", order_by="Interpretation.id")
    alleleassessments = relationship("AlleleAssessment", viewonly=True, secondary="analysisfinalized")

    __table_args__ = (ForeignKeyConstraint([genepanel_name, genepanel_version], ["genepanel.name", "genepanel.version"]),)

    def __repr__(self):
        return "<Analysis('%s, %s, %s')>" % (self.samples, self.genepanel_name, self.genepanel_version)


class Interpretation(Base):
    """Represents an Interpretation by a labengineer

    This corresponds to one interpretation 'round' of an analysis.
    The table stores both normal state and user-specific state for each round,
    while keeping a history of the state upon update.

    :note: The stateHistory column can potentially be heavy in extreme cases,
    so you can defer loading it when you don't need it.
    (TODO: defer by default?)
    """
    __tablename__ = "interpretation"

    id = Column(Integer, Sequence("id_interpretation_seq"), primary_key=True)
    analysis_id = Column(Integer, ForeignKey("analysis.id"), nullable=False)
    analysis = relationship("Analysis", uselist=False)
    user_state = Column("user_state", JSONMutableDict.as_mutable(JSONB), default={})
    user_id = Column(Integer, ForeignKey("user.id"))
    user = relationship("User", uselist=False, backref='interpretations')
    state = Column(JSONMutableDict.as_mutable(JSONB), default={})
    state_history = Column(JSONMutableDict.as_mutable(JSONB), default={})
    status = Column(Enum("Not started", "Ongoing", "Done", name="interpretation_status"),
                    default="Not started", nullable=False)
    date_last_update = Column(DateTime, nullable=False, default=datetime.datetime.now)

    def __repr__(self):
        return "<Interpretation('{}', '{}')>".format(str(self.analysis_id), self.status)
