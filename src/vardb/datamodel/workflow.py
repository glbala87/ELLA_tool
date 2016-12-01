#!/usr/bin/env python
"""varDB datamodel classes for entities that relate to samples."""

import datetime

from sqlalchemy import Column, Sequence, Integer, DateTime, Enum
from sqlalchemy import ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import JSONB

from vardb.datamodel import Base
from vardb.util.mutjson import JSONMutableDict


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

    id = Column(Integer, Sequence("id_alleleinterpretation_seq"), primary_key=True)
    allele_id = Column(Integer, ForeignKey("allele.id"), nullable=False)
    allele = relationship("Allele", uselist=False)
    user_state = Column("user_state", JSONMutableDict.as_mutable(JSONB), default={})
    user_id = Column(Integer, ForeignKey("user.id"))
    user = relationship("User", uselist=False)
    state = Column(JSONMutableDict.as_mutable(JSONB), default={})
    state_history = Column(JSONMutableDict.as_mutable(JSONB), default={})
    status = Column(Enum("Not started", "Ongoing", "Done", name="interpretation_status"),
                    default="Not started", nullable=False)
    date_last_update = Column(DateTime, nullable=False, default=datetime.datetime.now)

    def __repr__(self):
        return "<AlleleInterpretation('{}', '{}')>".format(str(self.allele_id), self.status)
