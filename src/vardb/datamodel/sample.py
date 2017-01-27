#!/usr/bin/env python
"""varDB datamodel classes for entities that relate to samples."""

import datetime

from sqlalchemy import Column, Integer, String, DateTime, Enum, Sequence
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

    id = Column(Integer, primary_key=True)
    identifier = Column(String(), nullable=False)
    analysis_id = Column(Integer, ForeignKey("analysis.id"), nullable=False)
    analysis = relationship('Analysis', backref='samples')
    sample_type = Column(Enum("HTS", "Sanger", name="sample_type"), nullable=False)
    deposit_date = Column(DateTime, nullable=False, default=datetime.datetime.now)
    sample_config = Column(JSONMutableDict.as_mutable(JSONB))  # includes capturekit and more

    __table_args__ = (Index("ix_sampleidentifier", "identifier"), )

    def __repr__(self):
        return "<Sample('%s', '%s')>" % (self.identifier, self.sample_type)


class Analysis(Base):
    """Represents a bioinformatical pipeline analysis

    An Analysis will have produced variant descriptions (e.g. VCF),
    that are an object for Interpretation.
    """
    __tablename__ = "analysis"

    id = Column(Integer, primary_key=True)
    name = Column(String(), nullable=False, unique=True)
    genepanel_name = Column(String)
    genepanel_version = Column(String)
    genepanel = relationship("Genepanel", uselist=False)
    deposit_date = Column("deposit_date", DateTime, nullable=False, default=datetime.datetime.now)
    analysis_config = Column(JSONMutableDict.as_mutable(JSONB))
    interpretations = relationship("AnalysisInterpretation", order_by="AnalysisInterpretation.id")
    properties = Column(JSONMutableDict.as_mutable(JSONB))  # Holds commments, tags etc
    priority = Column(Integer, nullable=False, default=1)
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


class AnnotationJob(Base):
    """
    Represents an annotation job submitted for annotation.

    This will be picked up by the annotation service polling thread, and sent to the annotation server.
    The feedback from the annotation server will be used to update the status and message-fields
    in the table.

    """
    __tablename__ = "annotationjob"

    id = Column(Integer, Sequence("id_job_seq"), primary_key=True)
    task_id = Column(String, default="")

    status = Column(Enum(
        "SUBMITTED",
        "RUNNING",
        "ANNOTATED",
        "CANCELLED",
        "DONE",
        "FAILED (SUBMISSION)",
        "FAILED (ANNOTATION)",
        "FAILED (DEPOSIT)",
        "FAILED (PROCESSING)",
        name="job_status"),
        default="SUBMITTED",
        nullable=False
    )
    status_history = Column(JSONMutableDict.as_mutable(JSONB), default={})
    mode = Column(Enum("Analysis", "Variants", name="mode"))
    vcf = Column(String, nullable=False)
    message = Column(String, default="")
    user_id = Column(Integer, ForeignKey("user.id"))
    user = relationship("User", uselist=False)
    date_submitted = Column(DateTime, nullable=False, default=datetime.datetime.now)
    date_last_update = Column(DateTime, nullable=False, default=datetime.datetime.now)

    properties = Column(JSONMutableDict.as_mutable(JSONB))

    """
    properties = dict(
        vcf="",
        error_message="",
        type="", # Analysis/Variants
        mode="",  # Append/Create
        genepanel="",
        analysis_name="",
        description="",
    )

    """

    def __repr__(self):
        return "<AnnotationJob('{}', '{}', '{}')".format(str(self.id), self.task_id, self.status)
