#!/usr/bin/env python
"""varDB datamodel classes for entities that relate to samples."""

import datetime
import pytz

from sqlalchemy import Column, Integer, String, DateTime, Enum, Boolean
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
    proband = Column(Boolean, nullable=False)
    family_id = Column(String())
    father_id = Column(Integer, ForeignKey("sample.id"))  # Set on proband
    mother_id = Column(Integer, ForeignKey("sample.id"))  # Set on proband
    sibling_id = Column(Integer, ForeignKey("sample.id"))  # Set for siblings pointing to proband (i.e. _not_ on proband)
    sex = Column(Enum("Male", "Female", name="sample_sex"))  # Can be unknown
    affected = Column(Boolean, nullable=False)  # Can be unknown
    deposit_date = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.datetime.now(pytz.utc))

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
    warnings = Column(String)
    report = Column(String)
    genepanel = relationship("Genepanel", uselist=False)
    deposit_date = Column("deposit_date", DateTime(timezone=True), nullable=False, default=lambda: datetime.datetime.now(pytz.utc))
    interpretations = relationship("AnalysisInterpretation", order_by="AnalysisInterpretation.id")
    properties = Column(JSONMutableDict.as_mutable(JSONB))  # Holds commments, tags etc
    __table_args__ = (ForeignKeyConstraint([genepanel_name, genepanel_version], ["genepanel.name", "genepanel.version"]),)

    def __repr__(self):
        return "<Analysis('%s, %s, %s')>" % (self.samples, self.genepanel_name, self.genepanel_version)


class FilterConfig(Base):

    """
    Represents a configuration of an analysis,
    e.g. ACMG configuration and filter configuration.

    Note that one analysis can utilise several AnalysisConfigs as part of
    a workflow/interpretation.
    """
    __tablename__ = "filterconfig"

    id = Column(Integer, primary_key=True)
    name = Column(String(), nullable=False, unique=True)
    filterconfig = Column(JSONMutableDict.as_mutable(JSONB), nullable=False)
    usergroup_id = Column(Integer, ForeignKey('usergroup.id'), nullable=False)
    default = Column(Boolean, nullable=False, default=False)
