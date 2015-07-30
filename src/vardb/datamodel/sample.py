
#!/usr/bin/env python
"""varDB datamodel classes for entities that relate to samples."""

import datetime

from sqlalchemy import Column, Sequence, Integer, String, DateTime, Enum
from sqlalchemy import ForeignKey
from sqlalchemy.orm import relationship, backref
from sqlalchemy.schema import Index, ForeignKeyConstraint
from sqlalchemy.dialects.postgresql import JSONB # For non-mutable values

from vardb.datamodel import Base
from vardb.datamodel import patient, gene
from vardb.util.mutjson import MUTJSONB

class Sample(Base):
    """Represents a sample (aka one sequencing run of 1 biological sample)

    Can represent samples from two types of technologies, Sanger and HTS.
    """
    __tablename__ = "sample"

    id = Column(Integer, Sequence("id_sample_seq"), primary_key=True)
    identifier = Column(String(), nullable=False) # SampleID in Swisslab
    sampleType = Column(Enum("HTS", "Sanger", name="sample_type"), nullable=False)
    patient_id = Column(Integer, ForeignKey("patient.id"))
    patient = relationship("Patient", backref=backref("samples", order_by=id))
    deposit_date = Column("deposit_date", DateTime, nullable=False, default=datetime.datetime.now)
    sampleConfig = Column("sample_config", JSONB) # includes capturekit and more

    __table_args__ = (Index("ix_sampleidentifier", "identifier", unique=True), )

    def __repr__(self):
        return "<Sample('%s', '%s','%s')>" % (self.identifier, self.patient, self.sampleType)


class Analysis(Base):
    """Represents a bioinformatical pipeline analysis

    An Analysis will have produced variant descriptions (e.g. VCF),
    that are an object for Interpretation.
    """
    __tablename__ = "analysis"

    id = Column(Integer, Sequence("id_analysis_seq"), primary_key=True)
    name = Column(String(), nullable=False)
    sample_id = Column(Integer, ForeignKey("sample.id"), nullable=False)
    sample = relationship("Sample", uselist=False)
    genepanelName = Column(String)
    genepanelVersion = Column(String)
    genepanel = relationship("Genepanel", uselist=False)
    deposit_date = Column("deposit_date", DateTime, nullable=False, default=datetime.datetime.now)
    analysisConfig = Column("analysis_config", JSONB)

    __table_args__ = (ForeignKeyConstraint([genepanelName, genepanelVersion], ["genepanel.name", "genepanel.version"]),)

    def __repr__(self):
        return "<Analysis('%s, %s, %s')>" % (self.sample, self.genepanelName, self.genepanelVersion)


class Interpretation(Base):
    """Represents an Interpretation by a labengineer

    This corresponds to one 'round' in the workbench.
    The table stores GUI-state.
    """
    __tablename__ = "interpretation"

    id = Column(Integer, Sequence("id_interpretation_seq"), primary_key=True)
    analysis_id = Column(Integer, ForeignKey("analysis.id"), nullable=False)
    analysis = relationship("Analysis", uselist=False, backref='interpretations')
    userState = Column("user_state", MUTJSONB, default={})
    user_id = Column(Integer, ForeignKey("user.id"))
    user = relationship("User", uselist=False, backref='interpretations')
    state = Column(MUTJSONB, default={})
    # TODO: Remove columns below and keep everything in guiState
    status = Column(Enum("Not started", "Ongoing", "Done", name="interpretation_status"),
                    default="Not started", nullable=False)
    dateLastUpdate = Column("date_last_update", DateTime, nullable=False, default=datetime.datetime.now)

    def __repr__(self):
        return "<Interpretation('{}', '{}')>".format(str(self.analysis_id), self.status)
