import datetime
import pytz
from sqlalchemy import Column, Integer, String, DateTime, Enum, Sequence, ForeignKeyConstraint
from sqlalchemy import ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import JSONB

from vardb.datamodel import Base
from vardb.util.mutjson import JSONMutableDict


class AnnotationJob(Base):
    """
    Represents an annotation job submitted for annotation.

    This will be picked up by the annotation service polling thread, and sent to the annotation server.
    The feedback from the annotation server will be used to update the status and message-fields
    in the table.

    """
    __tablename__ = "annotationjob"

    id = Column(Integer, primary_key=True)
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
    mode = Column(Enum("Analysis", "Variants", "Single variant", name="mode"))
    data = Column(String, nullable=False)
    message = Column(String, default="")
    user_id = Column(Integer, ForeignKey("user.id"))
    user = relationship("User", uselist=False)
    date_submitted = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.datetime.now(pytz.utc))
    date_last_update = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.datetime.now(pytz.utc))
    genepanel_name = Column(String)
    genepanel_version = Column(String)
    genepanel = relationship("Genepanel", uselist=False)

    properties = Column(JSONMutableDict.as_mutable(JSONB))

    __table_args__ = (ForeignKeyConstraint([genepanel_name, genepanel_version], ["genepanel.name", "genepanel.version"]),)

    def __repr__(self):
        return "<AnnotationJob('{}', '{}', '{}')".format(str(self.id), self.task_id, self.status)
