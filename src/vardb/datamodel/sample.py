#!/usr/bin/env python
"""varDB datamodel classes for entities that relate to samples."""

import datetime

from sqlalchemy import Column, Sequence, Integer, String, DateTime, Enum, Table
from sqlalchemy import ForeignKey
from sqlalchemy.orm import relationship, backref
from sqlalchemy.schema import Index, ForeignKeyConstraint
from sqlalchemy.dialects.postgresql import JSONB # For non-mutable values

from vardb.datamodel import Base
from vardb.datamodel import gene
from vardb.util.mutjson import MUTJSONB


# Tracks which alleleassessments was ultimately used for an analysis
# This is not to be confused with the analysis_id in AlleleAssessment table,
# which tells which analysis the AlleleAssessment was *created* for.
AnalysisAlleleAssessment = Table('analysisalleleassessment', Base.metadata,
    Column('analysis_id', Integer, ForeignKey('analysis.id')),
    Column('alleleassessment_id', Integer, ForeignKey('alleleassessment.id'))
)


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
    sample_config = Column(JSONB)  # includes capturekit and more

    __table_args__ = (Index("ix_sampleidentifier", "identifier"), )

    def __repr__(self):
        return "<Sample('%s', '%s')>" % (self.identifier, self.sample_type)


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
    analysis_config = Column(JSONB)
    interpretations = relationship("Interpretation", order_by="Interpretation.id")
    alleleassessments = relationship("AlleleAssessment", secondary=AnalysisAlleleAssessment)

    __table_args__ = (ForeignKeyConstraint([genepanel_name, genepanel_version], ["genepanel.name", "genepanel.version"]),)

    def __repr__(self):
        return "<Analysis('%s, %s, %s')>" % (self.samples, self.genepanel_name, self.genepanel_version)


class Interpretation(Base):
    """Represents an Interpretation by a labengineer

    This corresponds to one 'round' in the workbench.
    The table stores GUI-state.

    :note: The stateHistory column can potentially be heavy in extreme cases,
    so you can defer loading it when you don't need it.
    (TODO: defer by default?)
    """
    __tablename__ = "interpretation"

    id = Column(Integer, Sequence("id_interpretation_seq"), primary_key=True)
    analysis_id = Column(Integer, ForeignKey("analysis.id"), nullable=False)
    analysis = relationship("Analysis", uselist=False)
    user_state = Column("user_state", MUTJSONB, default={})
    user_id = Column(Integer, ForeignKey("user.id"))
    user = relationship("User", uselist=False, backref='interpretations')
    state = Column(MUTJSONB, default={})
    state_history = Column(MUTJSONB, default={})
    # TODO: Remove columns below and keep everything in guiState
    status = Column(Enum("Not started", "Ongoing", "Done", name="interpretation_status"),
                    default="Not started", nullable=False)
    date_last_update = Column(DateTime, nullable=False, default=datetime.datetime.now)

    def __repr__(self):
        return "<Interpretation('{}', '{}')>".format(str(self.analysis_id), self.status)
